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
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(root, "frontend", "frontend.html")
    return send_file(path)

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
            db_url = current_app.config.get("SQLALCHEMY_DATABASE_URI", os.path.join("app", "db.db"))
            import sqlite3
            conn = sqlite3.connect(db_url)
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
