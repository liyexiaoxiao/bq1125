from flask import request, jsonify, send_file, send_from_directory, current_app
import os
import threading
import time
import io
import zipfile
from ..base import base
from .. import setup_logger
from app.config import Config as DefaultConfig
from app.services.process_control import ProcessCtrl
from app.services.database_handler import TestResultHandler

_lock = threading.Lock()
_thread = None
_controller = None
_logger = setup_logger()
_status = {"running": False, "start_time": None, "base_run_id": None}

class AppConfigProxy:
    def __getattr__(self, name):
        try:
            # 动态构造平台接口URL
            if name in ("reset_api", "map_api", "read_api", "send_api"):
                base = current_app.config.get("TEST_PALTFORM_URL", getattr(DefaultConfig, "TEST_PALTFORM_URL", ""))
                suffix = {"reset_api": "reset", "map_api": "mapping", "read_api": "read", "send_api": "send"}[name]
                if base:
                    return f"{base}/api/v1/{suffix}"
            return current_app.config.get(name, getattr(DefaultConfig, name, None))
        except Exception:
            return getattr(DefaultConfig, name, None)

@base.route("/", methods=["GET"])
def serve_frontend():
    """服务前端页面
    优先返回Vite构建后的index.html，如果不存在则返回原始的frontend.html
    """
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    # 优先检查Vite构建产物
    vite_dist = os.path.join(root, "frontend", "dist", "index.html")
    if os.path.exists(vite_dist):
        return send_from_directory(os.path.join(root, "frontend", "dist"), "index.html")
    # 兜底：返回原始HTML
    path = os.path.join(root, "frontend", "frontend.html")
    return send_file(path)


@base.route("/assets/<path:filename>", methods=["GET"])
def serve_assets(filename):
    """服务Vite构建的静态资源"""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    assets_dir = os.path.join(root, "frontend", "dist", "assets")
    return send_from_directory(assets_dir, filename)

def _run_controller(app_obj):
    global _controller
    cfg = AppConfigProxy()
    _controller = ProcessCtrl(_logger, cfg, app_obj)
    try:
        _controller.run()
    finally:
        with _lock:
            _status["running"] = False
            _status["start_time"] = None
            _status["base_run_id"] = None

@base.route("/control/start", methods=["POST"])
def start_control():
    global _thread
    with _lock:
        if _status["running"]:
            return jsonify({"ok": 0, "message": "already running"}), 409
        _status["running"] = True
        _status["start_time"] = int(time.time())
        # 记录启动时的 run_id 基线
        try:
            db_path = current_app.config.get("DATABASE")
            if not db_path:
                db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", os.path.join("app", "db.db"))
                if db_url.startswith("sqlite:///"):
                    db_path = db_url.replace("sqlite:///", "")
                else:
                    db_path = db_url

            import sqlite3
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT MAX(run_id) FROM test_runs")
            row = cur.fetchone()
            _status["base_run_id"] = int(row[0]) if row and row[0] is not None else 0
        except Exception:
            _status["base_run_id"] = 0
        finally:
            try:
                conn.close()
            except Exception:
                pass
        _thread = threading.Thread(target=_run_controller, args=(current_app._get_current_object(),), daemon=True)
        _thread.start()
    return jsonify({"ok": 1})

@base.route("/control/stop", methods=["POST"])
def stop_control():
    with _lock:
        if not _status["running"]:
            return jsonify({"ok": 1, "message": "not running"}), 200
        if _controller:
            _controller.sing_stop = True
    return jsonify({"ok": 1})

@base.route("/control/status", methods=["GET"])
def control_status():
    running = False
    with _lock:
        running = _status["running"]
    db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", os.path.join("app", "db.db"))
    conn = None
    runs_since_start = 0
    exceptions_since_start = 0
    base_run_id = _status.get("base_run_id") or 0
    try:
        import sqlite3
        conn = sqlite3.connect(db_url)
        cur = conn.cursor()
        # 计算自启动以来新增条数
        cur.execute("SELECT MAX(run_id) FROM test_runs")
        row = cur.fetchone()
        latest_run_id = int(row[0]) if row and row[0] is not None else base_run_id
        runs_since_start = max(0, latest_run_id - base_run_id)
        # 计算自启动以来异常条数
        cur.execute("SELECT COUNT(1) FROM test_runs WHERE run_id > ? AND (status != 1 OR strategy < 0)", (base_run_id,))
        erow = cur.fetchone()
        exceptions_since_start = int(erow[0]) if erow and erow[0] is not None else 0
    except Exception:
        runs_since_start = 0
        exceptions_since_start = 0
    finally:
        if conn:
            conn.close()
    if not running:
        runs_since_start = 0
        exceptions_since_start = 0
    goal = getattr(DefaultConfig, "RUN_TIMES", 0)
    return jsonify({"running": running, "runs": runs_since_start, "goal": goal, "exceptions": exceptions_since_start})

def _tail_lines(file_path, max_lines):
    try:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 1024
            data = b""
            while size > 0 and len(data.splitlines()) <= max_lines:
                read_size = block if size >= block else size
                f.seek(size - read_size)
                data = f.read(read_size) + data
                size -= read_size
            lines = data.splitlines()[-max_lines:]
            return [line.decode("utf-8", errors="replace") for line in lines]
    except Exception:
        return []

@base.route("/logs/tail", methods=["GET"])
def tail_logs():
    lines = int(request.args.get("lines", "200"))
    path = _logger.all_log_file if hasattr(_logger, "all_log_file") else ""
    content = _tail_lines(path, lines)
    return jsonify({"path": path, "lines": content})

@base.route("/export", methods=["GET"])
def export_assets():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    files = []
    db_main = os.path.join(root, "app", "db.db")
    db_replay = os.path.join(root, "app", "replay.db")
    if os.path.exists(db_main):
        files.append(("app/db.db", db_main))
    if os.path.exists(db_replay):
        files.append(("app/replay.db", db_replay))
    logs_dir = os.path.join(root, "logs")
    if os.path.isdir(logs_dir):
        for name in os.listdir(logs_dir):
            p = os.path.join(logs_dir, name)
            if os.path.isfile(p):
                files.append((f"logs/{name}", p))
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, real in files:
            try:
                z.write(real, arc)
            except Exception:
                pass
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name="test_results.zip", mimetype="application/zip")


@base.route("/config/data", methods=["GET"])
def get_config():
    """获取当前配置"""
    # 从 DATABASE 配置中提取数据库名称
    database_path = getattr(DefaultConfig, "DATABASE", "app/db.db")
    # 提取文件名，去掉路径和后缀
    database_name = database_path.replace('app/', '').replace('app\\', '').replace('.db', '')
    
    config_data = {
        "testPlatformUrl": getattr(DefaultConfig, "TEST_PALTFORM_URL", ""),
        "runTimes": getattr(DefaultConfig, "RUN_TIMES", 1000),
        "mode": getattr(DefaultConfig, "MODE", "MIX"),
        "readInterval": getattr(DefaultConfig, "READ_INTERVAL", 100),
        "signalTolerance": getattr(DefaultConfig, "SIGNAL_TOLERANCE", 0.1),
        "singleVariationTime": getattr(DefaultConfig, "SINGLE_VARIATION_TIME", 10),
        "multipleVariationTime": getattr(DefaultConfig, "MULTIPLE_VARIATION_TIME", 10),
        "repeatVariationTime": getattr(DefaultConfig, "REPEAT_VARIATION_TIME", 20),
        "replayStartRunId": getattr(DefaultConfig, "REPLAY_START_RUN_ID", None),
        "replayEndRunId": getattr(DefaultConfig, "REPLAY_END_RUN_ID", None),
        "databaseName": database_name,
    }
    return jsonify(config_data)


@base.route("/config/data", methods=["POST"])
def save_config():
    """保存配置（运行时更新）"""
    data = request.get_json()
    if not data:
        return jsonify({"ok": 0, "message": "No data provided"}), 400
    
    # 映射前端字段到配置字段
    field_mapping = {
        "testPlatformUrl": "TEST_PALTFORM_URL",
        "runTimes": "RUN_TIMES",
        "mode": "MODE",
        "readInterval": "READ_INTERVAL",
        "signalTolerance": "SIGNAL_TOLERANCE",
        "singleVariationTime": "SINGLE_VARIATION_TIME",
        "multipleVariationTime": "MULTIPLE_VARIATION_TIME",
        "repeatVariationTime": "REPEAT_VARIATION_TIME",
        "replayStartRunId": "REPLAY_START_RUN_ID",
        "replayEndRunId": "REPLAY_END_RUN_ID",
    }
    
    for frontend_key, config_key in field_mapping.items():
        if frontend_key in data:
            setattr(DefaultConfig, config_key, data[frontend_key])
            current_app.config[config_key] = data[frontend_key]
    
    # 特殊处理数据库名称，构建完整路径
    if "databaseName" in data:
        db_name = data["databaseName"]
        db_path = os.path.join('app', f'{db_name}.db')
        
        # 更新所有相关的数据库配置
        setattr(DefaultConfig, "DATABASE", db_path)
        setattr(DefaultConfig, "SQLALCHEMY_DATABASE_URI", db_path)
        setattr(DefaultConfig, "REPLAY_SOURCE_DATABASE_URI", db_path)
        current_app.config["DATABASE"] = db_path
        current_app.config["SQLALCHEMY_DATABASE_URI"] = db_path
        current_app.config["REPLAY_SOURCE_DATABASE_URI"] = db_path
    
    return jsonify({"ok": 1, "message": "Config updated"})


@base.route("/charts/data", methods=["GET"])
def get_charts_data():
    """获取图表数据，从数据库读取 test_runs 表，包含 JSON 字段用于信号对比"""
    global _temp_db_path
    round_id = request.args.get("round_id", None)
    start_idx = request.args.get("start", 1, type=int)
    end_idx = request.args.get("end", 100, type=int)
    
    # 优先使用上传的数据库
    if _temp_db_path and os.path.exists(_temp_db_path):
        db_url = _temp_db_path
    else:
        db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", os.path.join("app", "db.db"))
    
    conn = None
    try:
        import sqlite3
        import json as json_module
        conn = sqlite3.connect(db_url)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # 获取所有轮次
        cur.execute("SELECT DISTINCT round_id FROM test_runs ORDER BY round_id")
        rounds = [row[0] for row in cur.fetchall()]
        
        # 计算 LIMIT 和 OFFSET
        limit = end_idx - start_idx + 1
        offset = start_idx - 1
        
        # 获取测试记录（包含 JSON 字段）
        if round_id:
            cur.execute("""
                SELECT run_id, round_id, type, status, strategy, expected_duration, actual_duration,
                       actual_input, expected_output, actual_output
                FROM test_runs 
                WHERE round_id = ? 
                ORDER BY run_id ASC 
                LIMIT ? OFFSET ?
            """, (round_id, limit, offset))
        else:
            cur.execute("""
                SELECT run_id, round_id, type, status, strategy, expected_duration, actual_duration,
                       actual_input, expected_output, actual_output
                FROM test_runs 
                ORDER BY run_id ASC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
        
        rows = cur.fetchall()
        records = []
        for row in rows:
            # 解析 JSON 字段
            actual_input = None
            expected_output = None
            actual_output = None
            
            try:
                if row[7]:
                    actual_input = json_module.loads(row[7]) if isinstance(row[7], str) else row[7]
            except:
                pass
            try:
                if row[8]:
                    expected_output = json_module.loads(row[8]) if isinstance(row[8], str) else row[8]
            except:
                pass
            try:
                if row[9]:
                    actual_output = json_module.loads(row[9]) if isinstance(row[9], str) else row[9]
            except:
                pass
            
            records.append({
                "run_id": row[0],
                "round_id": row[1],
                "type": row[2],
                "status": row[3],
                "strategy": row[4],
                "expected_duration": row[5],
                "actual_duration": row[6],
                "actual_input": actual_input,
                "expected_output": expected_output,
                "actual_output": actual_output
            })
        
        # 统计信息
        if round_id:
            cur.execute("SELECT COUNT(*) FROM test_runs WHERE round_id = ?", (round_id,))
        else:
            cur.execute("SELECT COUNT(*) FROM test_runs")
        total = cur.fetchone()[0]
        
        if round_id:
            cur.execute("SELECT COUNT(*) FROM test_runs WHERE round_id = ? AND status = 1", (round_id,))
        else:
            cur.execute("SELECT COUNT(*) FROM test_runs WHERE status = 1")
        normal = cur.fetchone()[0]
        
        if round_id:
            cur.execute("SELECT COUNT(*) FROM test_runs WHERE round_id = ? AND (status != 1 OR strategy < 0)", (round_id,))
        else:
            cur.execute("SELECT COUNT(*) FROM test_runs WHERE status != 1 OR strategy < 0")
        error = cur.fetchone()[0]
        
        if round_id:
            cur.execute("SELECT AVG(actual_duration) FROM test_runs WHERE round_id = ?", (round_id,))
        else:
            cur.execute("SELECT AVG(actual_duration) FROM test_runs")
        avg_row = cur.fetchone()
        avg_duration = round(avg_row[0], 2) if avg_row[0] else 0
        
        # 状态分布统计
        status_counts = {}
        for s in [1, 2, 3, 4]:
            if round_id:
                cur.execute("SELECT COUNT(*) FROM test_runs WHERE round_id = ? AND status = ?", (round_id, s))
            else:
                cur.execute("SELECT COUNT(*) FROM test_runs WHERE status = ?", (s,))
            status_counts[s] = cur.fetchone()[0]
        
        return jsonify({
            "rounds": rounds,
            "records": records,
            "stats": {
                "total": total,
                "normal": normal,
                "error": error,
                "avgDuration": avg_duration
            },
            "statusCounts": status_counts
        })
        
    except Exception as e:
        return jsonify({
            "rounds": [],
            "records": [],
            "stats": {"total": 0, "normal": 0, "error": 0, "avgDuration": 0},
            "statusCounts": {1: 0, 2: 0, 3: 0, 4: 0},
            "error": str(e)
        })
    finally:
        if conn:
            conn.close()


# 用于存储当前使用的临时数据库路径
_temp_db_path = None

@base.route("/charts/upload-db", methods=["POST"])
def upload_charts_db():
    """上传数据库文件用于图表展示"""
    global _temp_db_path
    
    if 'db_file' not in request.files:
        return jsonify({"ok": 0, "message": "No file provided"}), 400
    
    file = request.files['db_file']
    if file.filename == '':
        return jsonify({"ok": 0, "message": "No file selected"}), 400
    
    # 保存到临时目录
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    temp_dir = os.path.join(root, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 使用时间戳避免冲突
    import time as time_module
    filename = f"uploaded_{int(time_module.time())}_{file.filename}"
    temp_path = os.path.join(temp_dir, filename)
    file.save(temp_path)
    
    # 验证是否是有效的 SQLite 数据库
    try:
        import sqlite3
        conn = sqlite3.connect(temp_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_runs'")
        if not cur.fetchone():
            conn.close()
            os.remove(temp_path)
            return jsonify({"ok": 0, "message": "Database does not contain test_runs table"}), 400
        conn.close()
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"ok": 0, "message": f"Invalid database file: {str(e)}"}), 400
    
    # 保存临时数据库路径
    _temp_db_path = temp_path
    
    return jsonify({"ok": 1, "message": "Database uploaded successfully", "filename": filename})


def get_charts_db_path():
    """获取用于图表的数据库路径，优先使用上传的数据库"""
    global _temp_db_path
    if _temp_db_path and os.path.exists(_temp_db_path):
        return _temp_db_path
    return current_app.config.get("SQLALCHEMY_DATABASE_URI", os.path.join("app", "db.db"))
