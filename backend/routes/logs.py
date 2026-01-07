import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from datetime import datetime

from database import User
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/logs", tags=["日志管理"])


class LogFile(BaseModel):
    filename: str
    size: int
    modified: str
    type: str  # main, error, warn


class LogListResponse(BaseModel):
    files: List[LogFile]
    total: int


class LogContentResponse(BaseModel):
    filename: str
    content: str
    size: int
    lines: int


def get_log_type(filename: str) -> str:
    """Determine log type from filename"""
    if "_err" in filename:
        return "error"
    elif "_warn" in filename:
        return "warn"
    else:
        return "main"


@router.get("", response_model=LogListResponse)
async def list_logs(
    current_user: User = Depends(get_current_user),
    log_type: Optional[str] = Query(None, description="Filter by type: main, error, warn")
):
    """列出所有日志文件"""
    logs_dir = settings.LOGS_DIR
    
    if not os.path.exists(logs_dir):
        return LogListResponse(files=[], total=0)
    
    log_files = []
    for filename in os.listdir(logs_dir):
        if not filename.endswith(".log"):
            continue
        
        file_type = get_log_type(filename)
        
        # Filter by type if specified
        if log_type and file_type != log_type:
            continue
        
        filepath = os.path.join(logs_dir, filename)
        stat = os.stat(filepath)
        
        log_files.append(LogFile(
            filename=filename,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            type=file_type
        ))
    
    # Sort by modified time (newest first)
    log_files.sort(key=lambda x: x.modified, reverse=True)
    
    return LogListResponse(files=log_files, total=len(log_files))


@router.get("/latest", response_model=LogContentResponse)
async def get_latest_log(
    current_user: User = Depends(get_current_user),
    lines: int = Query(100, description="Number of lines to return from end"),
    log_type: str = Query("main", description="Log type: main, error, warn")
):
    """获取最新的日志文件内容"""
    logs_dir = settings.LOGS_DIR
    
    if not os.path.exists(logs_dir):
        raise HTTPException(status_code=404, detail="日志目录不存在")
    
    # Find the latest log file of specified type
    log_files = []
    for filename in os.listdir(logs_dir):
        if not filename.endswith(".log"):
            continue
        if get_log_type(filename) != log_type:
            continue
        
        filepath = os.path.join(logs_dir, filename)
        stat = os.stat(filepath)
        log_files.append((filename, stat.st_mtime))
    
    if not log_files:
        raise HTTPException(status_code=404, detail="没有找到日志文件")
    
    # Get the most recent file
    log_files.sort(key=lambda x: x[1], reverse=True)
    latest_file = log_files[0][0]
    
    filepath = os.path.join(logs_dir, latest_file)
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        
        # Get last N lines
        content_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        content = ''.join(content_lines)
        
        return LogContentResponse(
            filename=latest_file,
            content=content,
            size=os.path.getsize(filepath),
            lines=len(content_lines)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志失败: {str(e)}")


@router.get("/{filename}", response_model=LogContentResponse)
async def get_log_content(
    filename: str,
    current_user: User = Depends(get_current_user),
    lines: int = Query(500, description="Number of lines to return from end"),
    offset: int = Query(0, description="Line offset from end")
):
    """获取指定日志文件内容"""
    logs_dir = settings.LOGS_DIR
    filepath = os.path.join(logs_dir, filename)
    
    # Security check - prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="日志文件不存在")
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        
        # Get specified range of lines
        total = len(all_lines)
        end_idx = total - offset if offset > 0 else total
        start_idx = max(0, end_idx - lines)
        
        content_lines = all_lines[start_idx:end_idx]
        content = ''.join(content_lines)
        
        return LogContentResponse(
            filename=filename,
            content=content,
            size=os.path.getsize(filepath),
            lines=len(content_lines)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志失败: {str(e)}")
