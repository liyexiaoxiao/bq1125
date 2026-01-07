import os
import json
import sqlite3
import base64
import io
import shutil
from typing import List, Optional, Dict, Any
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from database import User
from auth import get_current_user
from config import settings

# Configure Chinese font support
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "DejaVu Sans"]
plt.rcParams['axes.unicode_minus'] = False

router = APIRouter(prefix="/api/charts", tags=["图表分析"])

# Store for custom uploaded DB paths (per session, in production use Redis/database)
_custom_db_path: Optional[str] = None


class SignalTrendRequest(BaseModel):
    batch_size: int = 100
    batch_num: Optional[int] = None  # If None, generate all batches


class ComparisonRequest(BaseModel):
    signal_name1: str
    signal_name2: str
    batch_size: int = 100
    batch_num: Optional[int] = None


class ChartResponse(BaseModel):
    charts: List[Dict[str, Any]]  # List of {name, image_base64, batch_num}
    total_batches: int


class SignalListResponse(BaseModel):
    signals: List[str]


class UploadResponse(BaseModel):
    message: str
    filename: str
    records: int


class DataSourceResponse(BaseModel):
    current_source: str
    is_custom: bool


def get_db_connection(custom_path: Optional[str] = None):
    """Get connection to replay.db or custom uploaded db"""
    global _custom_db_path
    
    if custom_path:
        db_path = custom_path
    elif _custom_db_path:
        db_path = _custom_db_path
    else:
        db_path = settings.APP_DB_PATH
    
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail=f"数据库文件不存在: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_test_runs(custom_path: Optional[str] = None):
    """Get all test runs from database"""
    conn = get_db_connection(custom_path)
    try:
        runs = conn.execute('SELECT * FROM test_runs').fetchall()
        return [dict(run) for run in runs]
    finally:
        conn.close()


def extract_signal_names(runs: List[dict]) -> List[str]:
    """Extract all unique signal names from test runs"""
    signal_names = set()
    for run in runs:
        actual_output_str = run.get('actual_output', '')
        if not actual_output_str:
            continue
        try:
            actual_output = json.loads(actual_output_str)
            data_list = actual_output.get("data", [])
            for item in data_list:
                name = item.get("name")
                if name:
                    signal_names.add(name)
        except (json.JSONDecodeError, TypeError):
            continue
    return sorted(list(signal_names))


def detect_extrema(values: List[float]):
    """Detect extrema points (maxima and minima)"""
    if len(values) < 3:
        return [], []
    
    maxima = []
    minima = []
    
    for i in range(1, len(values) - 1):
        if values[i] > values[i-1] and values[i] > values[i+1]:
            maxima.append(i)
        elif values[i] < values[i-1] and values[i] < values[i+1]:
            minima.append(i)
    
    return maxima, minima


def compare_trends(values1: List[float], values2: List[float], tolerance: int = 1):
    """Compare trend patterns between two signals"""
    maxima1, minima1 = detect_extrema(values1)
    maxima2, minima2 = detect_extrema(values2)
    
    anomaly_indices = []
    
    for idx1 in maxima1:
        if not any(abs(idx1 - idx2) <= tolerance for idx2 in maxima2):
            anomaly_indices.append(idx1)
    
    for idx1 in minima1:
        if not any(abs(idx1 - idx2) <= tolerance for idx2 in minima2):
            anomaly_indices.append(idx1)
    
    for idx2 in maxima2:
        if not any(abs(idx2 - idx1) <= tolerance for idx1 in maxima1):
            if idx2 not in anomaly_indices:
                anomaly_indices.append(idx2)
    
    for idx2 in minima2:
        if not any(abs(idx2 - idx1) <= tolerance for idx1 in minima1):
            if idx2 not in anomaly_indices:
                anomaly_indices.append(idx2)
    
    return sorted(set(anomaly_indices))


def fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


@router.post("/upload-db", response_model=UploadResponse)
async def upload_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传自定义数据库文件用于分析"""
    global _custom_db_path
    
    if not file.filename.endswith('.db'):
        raise HTTPException(status_code=400, detail="只支持 .db 文件")
    
    # Create uploads directory if not exists
    upload_dir = os.path.join(settings.PROJECT_ROOT, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file
    file_path = os.path.join(upload_dir, f"custom_{file.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    # Verify it's a valid SQLite database with test_runs table
    try:
        conn = sqlite3.connect(file_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT COUNT(*) as count FROM test_runs")
        record_count = cursor.fetchone()['count']
        conn.close()
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"无效的数据库文件: {str(e)}")
    
    # Set as current custom DB
    _custom_db_path = file_path
    
    return UploadResponse(
        message="数据库上传成功",
        filename=file.filename,
        records=record_count
    )


@router.post("/reset-db")
async def reset_database(current_user: User = Depends(get_current_user)):
    """恢复使用默认数据库"""
    global _custom_db_path
    _custom_db_path = None
    return {"message": "已恢复使用默认数据库", "source": settings.APP_DB_PATH}


@router.get("/data-source", response_model=DataSourceResponse)
async def get_data_source(current_user: User = Depends(get_current_user)):
    """获取当前数据源信息"""
    global _custom_db_path
    
    if _custom_db_path:
        return DataSourceResponse(
            current_source=os.path.basename(_custom_db_path),
            is_custom=True
        )
    else:
        return DataSourceResponse(
            current_source=os.path.basename(settings.APP_DB_PATH),
            is_custom=False
        )


@router.get("/signals", response_model=SignalListResponse)
async def list_signals(current_user: User = Depends(get_current_user)):
    """获取所有可用的信号名称列表"""
    try:
        runs = get_all_test_runs()
        signals = extract_signal_names(runs)
        return SignalListResponse(signals=signals)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取信号列表失败: {str(e)}")


@router.post("/signal-trends", response_model=ChartResponse)
async def generate_signal_trends(
    request: SignalTrendRequest,
    current_user: User = Depends(get_current_user)
):
    """生成单信号趋势图 (get100.py 逻辑)"""
    try:
        runs = get_all_test_runs()
        total_runs = len(runs)
        
        if total_runs == 0:
            return ChartResponse(charts=[], total_batches=0)
        
        batch_size = request.batch_size
        batches = [(i, min(i + batch_size, total_runs)) for i in range(0, total_runs, batch_size)]
        total_batches = len(batches)
        
        charts = []
        
        # If specific batch requested, only generate that one
        batch_range = [request.batch_num - 1] if request.batch_num else range(len(batches))
        
        for batch_idx in batch_range:
            if batch_idx < 0 or batch_idx >= len(batches):
                continue
                
            start_idx, end_idx = batches[batch_idx]
            batch_runs = runs[start_idx:end_idx]
            batch_num = batch_idx + 1
            
            # Collect data by signal name
            name_data = defaultdict(list)
            
            for idx, run in enumerate(batch_runs):
                run_id = run.get('id', start_idx + idx)
                actual_output_str = run.get('actual_output', '')
                
                if not actual_output_str:
                    continue
                
                try:
                    actual_output = json.loads(actual_output_str)
                    data_list = actual_output.get("data", [])
                    
                    for item in data_list:
                        name = item.get("name")
                        value = item.get("value")
                        if name is not None and value is not None:
                            name_data[name].append((run_id, value))
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Generate chart for each signal
            for name, points in name_data.items():
                if len(points) == 0:
                    continue
                
                points.sort(key=lambda x: x[0])
                x_vals = [p[0] for p in points]
                y_vals = [p[1] for p in points]
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(x_vals, y_vals, marker='o', linestyle='-', label=name)
                ax.set_title(f'"{name}" 值随测试轮次变化曲线 (批次 {batch_num})')
                ax.set_xlabel('Run ID')
                ax.set_ylabel('Value')
                ax.grid(True)
                ax.legend()
                plt.tight_layout()
                
                image_base64 = fig_to_base64(fig)
                plt.close(fig)
                
                charts.append({
                    "name": name,
                    "image_base64": image_base64,
                    "batch_num": batch_num
                })
        
        return ChartResponse(charts=charts, total_batches=total_batches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成图表失败: {str(e)}")


@router.post("/comparison", response_model=ChartResponse)
async def generate_comparison_charts(
    request: ComparisonRequest,
    current_user: User = Depends(get_current_user)
):
    """生成信号对比图 (异常状态对比图_极值对比.py 逻辑)"""
    try:
        runs = get_all_test_runs()
        total_runs = len(runs)
        
        if total_runs == 0:
            return ChartResponse(charts=[], total_batches=0)
        
        name1 = request.signal_name1
        name2 = request.signal_name2
        batch_size = request.batch_size
        
        batches = [(i, min(i + batch_size, total_runs)) for i in range(0, total_runs, batch_size)]
        total_batches = len(batches)
        
        charts = []
        
        batch_range = [request.batch_num - 1] if request.batch_num else range(len(batches))
        
        for batch_idx in batch_range:
            if batch_idx < 0 or batch_idx >= len(batches):
                continue
                
            start_idx, end_idx = batches[batch_idx]
            batch_runs = runs[start_idx:end_idx]
            batch_num = batch_idx + 1
            
            data = {name1: [], name2: []}
            
            for idx, run in enumerate(batch_runs):
                data_index = start_idx + idx + 1
                actual_output_str = run.get('actual_output', '')
                
                if not actual_output_str:
                    continue
                
                try:
                    actual_output = json.loads(actual_output_str)
                    data_list = actual_output.get("data", [])
                    
                    current_values = {name1: None, name2: None}
                    for item in data_list:
                        if item.get("name") == name1:
                            current_values[name1] = item.get("value")
                        elif item.get("name") == name2:
                            current_values[name2] = item.get("value")
                    
                    if current_values[name1] is not None and current_values[name2] is not None:
                        data[name1].append((data_index, current_values[name1]))
                        data[name2].append((data_index, current_values[name2]))
                except (json.JSONDecodeError, TypeError):
                    continue
            
            if not data[name1] or not data[name2]:
                continue
            
            for name in data:
                data[name].sort(key=lambda x: x[0])
            
            indices1 = {p[0] for p in data[name1]}
            indices2 = {p[0] for p in data[name2]}
            common_indices = indices1 & indices2
            
            common_data1 = sorted([p for p in data[name1] if p[0] in common_indices], key=lambda x: x[0])
            common_data2 = sorted([p for p in data[name2] if p[0] in common_indices], key=lambda x: x[0])
            
            values1 = [p[1] for p in common_data1]
            values2 = [p[1] for p in common_data2]
            
            maxima1, minima1 = detect_extrema(values1)
            maxima2, minima2 = detect_extrema(values2)
            trend_anomaly_indices = compare_trends(values1, values2, tolerance=1)
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot([p[0] for p in common_data1], values1, marker='o', linestyle='-', label=name1, alpha=0.7)
            ax.plot([p[0] for p in common_data2], values2, marker='s', linestyle='--', label=name2, alpha=0.7)
            
            # Mark extrema
            for local_idx in maxima1:
                if local_idx < len(common_data1):
                    ax.plot(common_data1[local_idx][0], values1[local_idx], 'r^', markersize=10)
            
            for local_idx in minima1:
                if local_idx < len(common_data1):
                    ax.plot(common_data1[local_idx][0], values1[local_idx], 'rv', markersize=10)
            
            for local_idx in maxima2:
                if local_idx < len(common_data2):
                    ax.plot(common_data2[local_idx][0], values2[local_idx], 'b^', markersize=10)
            
            for local_idx in minima2:
                if local_idx < len(common_data2):
                    ax.plot(common_data2[local_idx][0], values2[local_idx], 'bv', markersize=10)
            
            # Mark anomalies
            for local_idx in trend_anomaly_indices:
                if local_idx < len(common_data1):
                    ax.axvline(x=common_data1[local_idx][0], color='red', linestyle=':', alpha=0.5)
            
            anomaly_count = len(trend_anomaly_indices)
            title_info = f'(异常: {anomaly_count}处)' if anomaly_count > 0 else '(趋势一致)'
            
            ax.set_title(f'{name1} vs {name2} 趋势对比 (批次 {batch_num}) {title_info}')
            ax.set_xlabel('数据序号')
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3)
            ax.legend()
            plt.tight_layout()
            
            image_base64 = fig_to_base64(fig)
            plt.close(fig)
            
            charts.append({
                "name": f"{name1} vs {name2}",
                "image_base64": image_base64,
                "batch_num": batch_num,
                "anomaly_count": anomaly_count
            })
        
        return ChartResponse(charts=charts, total_batches=total_batches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成对比图失败: {str(e)}")
