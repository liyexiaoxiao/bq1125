import os
import subprocess
import signal
import sys
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import User
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/process", tags=["进程控制"])

# Global process reference
_process: Optional[subprocess.Popen] = None


import re
import sqlite3
from fastapi.responses import FileResponse

class ProcessStatus(BaseModel):
    running: bool
    pid: Optional[int] = None
    message: str
    current_round: Optional[int] = 0
    total_rounds: Optional[int] = 0
    progress: Optional[float] = 0.0


@router.get("/status", response_model=ProcessStatus)
async def get_process_status(current_user: User = Depends(get_current_user)):
    """获取测试进程状态"""
    global _process
    
    running = False
    pid = None
    message = "进程未启动"
    
    if _process is not None:
        poll_result = _process.poll()
        if poll_result is None:
            running = True
            pid = _process.pid
            message = "测试运行中"
        else:
            message = f"进程已结束，退出码: {poll_result}"
            
    # Get progress
    current_round = 0
    total_rounds = 0
    
    # Read total_rounds from config
    config_path = settings.CONFIG_FILE_PATH
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'RUN_TIMES\s*=\s*(\d+)', content)
                if match:
                    total_rounds = int(match.group(1))
        except:
            pass
            
    # Read current_round from db
    db_path = settings.APP_DB_PATH
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM test_runs")
            row = cursor.fetchone()
            if row:
                current_round = row[0]
            conn.close()
        except:
            pass
            
    progress = 0.0
    if total_rounds > 0:
        progress = min(round(current_round / total_rounds * 100, 1), 100.0)
    
    return ProcessStatus(
        running=running,
        pid=pid,
        message=message,
        current_round=current_round,
        total_rounds=total_rounds,
        progress=progress
    )


@router.post("/start", response_model=ProcessStatus)
async def start_process(current_user: User = Depends(get_current_user)):
    """启动测试进程 (运行 start.py)"""
    global _process
    
    # Check if already running
    if _process is not None:
        poll_result = _process.poll()
        if poll_result is None:
            raise HTTPException(
                status_code=400,
                detail="测试进程已在运行中"
            )
    
    start_py_path = settings.START_PY_PATH
    if not os.path.exists(start_py_path):
        raise HTTPException(
            status_code=404,
            detail=f"start.py 文件不存在: {start_py_path}"
        )
    
    try:
        # Clear database before starting
        db_path = settings.APP_DB_PATH
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check for tables and clear them
                tables = ["test_runs", "pro_input", "test_error_log"]
                for table in tables:
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    except:
                        pass # Table might not exist
                        
                conn.commit()
                conn.close()
            except Exception as db_e:
                print(f"Failed to clear database: {db_e}")

        # Get the project root directory
        project_root = settings.PROJECT_ROOT
        
        # Ensure logs directory exists
        logs_dir = settings.LOGS_DIR
        os.makedirs(logs_dir, exist_ok=True)
        
        stdout_path = os.path.join(logs_dir, "process_stdout.log")
        stderr_path = os.path.join(logs_dir, "process_stderr.log")
        
        stdout_file = open(stdout_path, "w", encoding="utf-8")
        stderr_file = open(stderr_path, "w", encoding="utf-8")

        # Cleanup potential zombie processes
        if sys.platform != "win32":
            try:
                # kill any process containing 'start.py' (except backend itself if it matched, but backend is uvicorn)
                # Using -f to match full command line
                subprocess.run("pkill -9 -f start.py", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        # Start the process
        if sys.platform == "win32":
            # Windows: use CREATE_NEW_PROCESS_GROUP for proper signal handling
            _process = subprocess.Popen(
                [sys.executable, start_py_path],
                cwd=project_root,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=stdout_file,
                stderr=stderr_file,
                env=env
            )
        else:
            # Unix: use process group
            _process = subprocess.Popen(
                [sys.executable, start_py_path],
                cwd=project_root,
                stdout=stdout_file,
                stderr=stderr_file,
                preexec_fn=os.setsid,
                env=env
            )
        
        # Return initial status
        return await get_process_status(current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"启动进程失败: {str(e)}"
        )


@router.post("/stop", response_model=ProcessStatus)
async def stop_process(current_user: User = Depends(get_current_user)):
    """停止测试进程 (相当于 Ctrl+C)"""
    global _process
    
    if _process is None:
        return await get_process_status(current_user)
    
    poll_result = _process.poll()
    if poll_result is not None:
        _process = None
        return await get_process_status(current_user)
    
    try:
        pid = _process.pid
        
        if sys.platform == "win32":
            # Windows: send CTRL_BREAK_EVENT
            os.kill(pid, signal.CTRL_BREAK_EVENT)
        else:
            # Unix: send SIGINT (Ctrl+C equivalent)
            os.killpg(os.getpgid(pid), signal.SIGINT)
        
        # Wait a bit for graceful shutdown
        try:
            _process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if not responding
            _process.kill()
            _process.wait()
        
        _process = None
        return await get_process_status(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"停止进程失败: {str(e)}"
        )


@router.get("/export")
async def export_data(current_user: User = Depends(get_current_user)):
    """导出数据库文件"""
    db_path = settings.APP_DB_PATH
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="数据库文件不存在")
        
    return FileResponse(
        path=db_path,
        filename="test_results.db",
        media_type='application/x-sqlite3'
    )


@router.get("/output")
async def get_process_output(current_user: User = Depends(get_current_user)):
    """获取进程的标准输出和错误输出（从日志文件读取）"""
    global _process
    
    logs_dir = settings.LOGS_DIR
    stdout_path = os.path.join(logs_dir, "process_stdout.log")
    stderr_path = os.path.join(logs_dir, "process_stderr.log")
    
    stdout_data = ""
    stderr_data = ""
    
    if os.path.exists(stdout_path):
        try:
            with open(stdout_path, "r", encoding="utf-8", errors="replace") as f:
                # 只读取最后 2000 字符
                f.seek(0, os.SEEK_END)
                size = f.tell()
                read_size = min(size, 2000)
                f.seek(size - read_size)
                stdout_data = f.read()
        except:
            pass

    if os.path.exists(stderr_path):
        try:
            with open(stderr_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                read_size = min(size, 2000)
                f.seek(size - read_size)
                stderr_data = f.read()
        except:
            pass
            
    running = False
    exit_code = None
    if _process:
        exit_code = _process.poll()
        running = exit_code is None
    
    return {
        "stdout": stdout_data,
        "stderr": stderr_data,
        "running": running,
        "exit_code": exit_code,
        "cwd": settings.PROJECT_ROOT,
        "start_py": settings.START_PY_PATH,
        "logs_dir": logs_dir
    }


@router.get("/test-run")
async def test_run_process(current_user: User = Depends(get_current_user)):
    """测试运行 start.py 并返回完整输出（同步等待完成）"""
    start_py_path = settings.START_PY_PATH
    project_root = settings.PROJECT_ROOT
    
    if not os.path.exists(start_py_path):
        return {"error": f"start.py 不存在: {start_py_path}"}
    
    try:
        # Run synchronously and capture all output
        result = subprocess.run(
            [sys.executable, start_py_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout,
            "stderr": result.stderr[-3000:] if len(result.stderr) > 3000 else result.stderr,
            "cwd": project_root,
            "python": sys.executable
        }
    except subprocess.TimeoutExpired:
        return {"error": "进程超时 (30秒)", "cwd": project_root}
    except Exception as e:
        return {"error": str(e), "cwd": project_root}

