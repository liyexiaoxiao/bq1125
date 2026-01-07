"""
Mock Test Platform Server
模拟被测平台的 API 服务

运行方式:
  pip install flask
  python mock_platform.py

默认运行在 http://0.0.0.0:8020
"""

from flask import Flask, request, jsonify
import random
import time
import json

app = Flask(__name__)

# 模拟的信号数据
# 模拟的信号数据
MOCK_SIGNALS = {
    "快充唤醒信号": {"min": 0, "max": 1, "type": "int"},
    "整车状态": {"values": [30, 170], "type": "choice"},
    "SOC": {"min": 0, "max": 100, "type": "float"},
    "电池电压": {"min": 300, "max": 420, "type": "float"},
    "电池电流": {"min": -200, "max": 200, "type": "float"},
    "电池温度": {"min": -20, "max": 60, "type": "float"},
    "充电状态": {"min": 0, "max": 3, "type": "int"},
    "BMS故障码": {"min": 0, "max": 0, "type": "int"},
    "绝缘电阻": {"min": 500, "max": 2000, "type": "float"},
}

# 存储当前状态
current_state = {}


def generate_signal_value(signal_name):
    """生成信号值"""
    config = MOCK_SIGNALS.get(signal_name, {"min": 0, "max": 100, "type": "float"})
    
    if config.get("type") == "choice":
        return random.choice(config["values"])
    elif config["type"] == "int":
        return random.randint(config["min"], config["max"])
    else:
        return round(random.uniform(config["min"], config["max"]), 2)


@app.route('/')
def index():
    return jsonify({
        "message": "Mock Test Platform API",
        "version": "1.0.0",
        "status": "running"
    })


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "healthy", "timestamp": time.time()})


@app.route('/api/signals', methods=['GET'])
def get_signals():
    """获取所有信号列表"""
    return jsonify({
        "code": 200,
        "data": list(MOCK_SIGNALS.keys())
    })


@app.route('/api/read', methods=['GET', 'POST'])
@app.route('/api/v1/read', methods=['GET', 'POST'])
def read_signals():
    """读取信号值 - 模拟 Fuzz 测试读取"""
    # 生成随机信号数据
    data = {}
    for name in MOCK_SIGNALS.keys():
        value = generate_signal_value(name)
        current_state[name] = value
        data[name] = value
    
    # 适配 bq_api.py 的响应结构: {"ok": 1, "data": ...}
    return jsonify({
        "code": 200,
        "msg": "success",
        "ok": 1,
        "data": data
    })


@app.route('/api/write', methods=['POST'])
@app.route('/api/v1/write', methods=['POST'])
@app.route('/api/send', methods=['POST'])
@app.route('/api/v1/send', methods=['POST'])
def write_signals():
    """写入信号值 - 模拟 Fuzz 测试变异输入"""
    try:
        payload = request.get_json() or {}
        # 兼容列表或字典格式
        signals = payload.get("signals", []) if isinstance(payload, dict) else []
        
        # 如果直接是键值对
        if isinstance(payload, dict) and not signals:
             for k, v in payload.items():
                 current_state[k] = v
        
        time.sleep(random.uniform(5, 10))
        
        return jsonify({
            "code": 200,
            "msg": "success",
            "ok": 1,
            "written": len(signals)
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str(e),
            "ok": 0
        }), 500


@app.route('/api/execute', methods=['POST'])
@app.route('/api/v1/execute', methods=['POST'])
def execute_test():
    """执行测试用例"""
    try:
        payload = request.get_json() or {}
        test_case = payload.get("test_case", {})
        
        # 模拟执行时间
        time.sleep(random.uniform(0.1, 0.5))
        
        # 生成随机结果
        passed = random.random() > 0.1  # 90% 通过率
        
        # 生成输出数据
        actual_output = {
            "data": {name: generate_signal_value(name) for name in MOCK_SIGNALS.keys()}
        }
        
        return jsonify({
            "code": 200,
            "msg": "test executed",
            "ok": 1,
            "result": {
                "passed": passed,
                "actual_output": actual_output,
                "expected_output": test_case.get("expected", {}),
                "execution_time": random.uniform(0.1, 0.5)
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str(e),
            "ok": 0
        }), 500


@app.route('/api/status', methods=['GET'])
@app.route('/api/v1/status', methods=['GET'])
def get_status():
    """获取平台状态"""
    return jsonify({
        "code": 200,
        "ok": 1,
        "data": {
            "platform": "mock",
            "connected": True,
            "current_state": current_state,
            "uptime": time.time()
        }
    })


@app.route('/api/reset', methods=['POST'])
@app.route('/api/v1/reset', methods=['POST'])
def reset_platform():
    """重置平台状态"""
    global current_state
    current_state = {}
    return jsonify({
        "code": 200,
        "msg": "Platform reset successfully",
        "ok": 1
    })


# 兼容原有 API 格式
@app.route('/krun/api/v1/read', methods=['GET', 'POST'])
def krun_read():
    """兼容 krunapi 格式的读取接口"""
    return read_signals()


@app.route('/krun/api/v1/write', methods=['POST'])
def krun_write():
    """兼容 krunapi 格式的写入接口"""
    return write_signals()


@app.route('/krun/api/v1/execute', methods=['POST'])
def krun_execute():
    """兼容 krunapi 格式的执行接口"""
    return execute_test()


@app.route('/api/mapping', methods=['POST'])
@app.route('/api/v1/mapping', methods=['POST'])
def get_mapping():
    """获取映射"""
    return jsonify({
        "code": 200,
        "msg": "success",
        "ok": 1,
        "data": {}
    })


if __name__ == '__main__':
    print("=" * 50)
    print("Mock Test Platform Server")
    print("=" * 50)
    print("Running on http://0.0.0.0:8020")
    print("Available endpoints:")
    print("  GET  /api/health     - Health check")
    print("  GET  /api/signals    - List all signals")
    print("  GET  /api/read       - Read signal values")
    print("  POST /api/write      - Write signal values")
    print("  POST /api/execute    - Execute test case")
    print("  GET  /api/status     - Platform status")
    print("  POST /api/reset      - Reset platform")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8020, debug=False, use_reloader=False)
