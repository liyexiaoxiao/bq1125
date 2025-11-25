#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模拟API服务器，用于测试 ResultJudge 类
根据提供的测试数据生成符合预期和错误情况的响应
"""

import json
import random
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
# 模拟数据
mock_data = {
    "ok": {
      "ok": 1,
      "msg": "提示信息",
      "data": {}
    },
    "get": {
        "ok": 1,
        "msg": "提示信息",
        "data": [
            {"id": 1, "name": "Alice", "age": 25},
            {"id": 2, "name": "Bob", "age": 30},
            {"id": 3, "name": "Charlie", "age": 35},
            ]
    },
    "no": {
      "ok": 1,
      "msg": "提示信息",
      "data": {}
    },
}
num = 0
# 存储信号值的字典
signal_values = {}
# 测试数据
test_data = {
    "type": 1,
    "in_data": [{
        "name": "供电电压",
        "data_type": "float",
        "value": "9.3",
        "ID": "2ba96003-14dc-11f0-a0b8-6c0b84df158f"
    }],
    "expected_results":[{
        "name": "功耗电流",
        "uuid": "630c86f7-14dd-11f0-ad8e-6c0b84df158f",
        "out_type": 1,
        "out_range": 1,
        "value": 0.05
    }, {
        "name": "整车State状态",
        "uuid": "35695f8f-14dd-11f0-a9e0-6c0b84df158f",
        "out_type": 1,
        "out_range": 2,
        "value": 11
    }, {
        "name": "总线报文发送标志位",
        "uuid": "b0bf7c0b-14dd-11f0-a72f-6c0b84df158f",
        "out_type": 1,
        "out_range": 2,
        "value": 1
    }, {
        "name": "PDCU唤醒原因",
        "uuid": "c8391a2f-14dd-11f0-b145-6c0b84df158f",
        "out_type": 1,
        "out_range": 2,
        "value": 1
    }, {
        "name": "整车模式",
        "uuid": "14b7c71b-14df-11f0-8f04-6c0b84df158f",
        "out_type": 1,
        "out_range": 2,
        "value": 2
    }],
    "error": [{
        "error_type": 1,
        "out_data": [{
            "name": "功耗电流",
            "uuid": "630c86f7-14dd-11f0-ad8e-6c0b84df158f",
            "out_type": 1,
            "out_range": 3,
            "value": 0.05
        },{
            "name": "总线报文发送标志位",
            "uuid": "b0bf7c0b-14dd-11f0-a72f-6c0b84df158f",
            "out_type": 1,
            "out_range": 2,
            "value": 0
        }]
    },{
        "error_type": 2,
        "out_data": [{
            "name": "功耗电流",
            "uuid": "630c86f7-14dd-11f0-ad8e-6c0b84df158f",
            "out_type": 1,
            "out_range": 1,
            "value": 0.05
        }, {
            "name": "整车State状态",
            "uuid": "35695f8f-14dd-11f0-a9e0-6c0b84df158f",
            "out_type": 1,
            "out_range": 2,
            "value": 10
        }, {
            "name": "总线报文发送标志位",
            "uuid": "b0bf7c0b-14dd-11f0-a72f-6c0b84df158f",
            "out_type": 1,
            "out_range": 2,
            "value": 1
        }, {
            "name": "PDCU唤醒原因",
            "uuid": "c8391a2f-14dd-11f0-b145-6c0b84df158f",
            "out_type": 1,
            "out_range": 2,
            "value": 1
        }, {
            "name": "整车模式",
            "uuid": "14b7c71b-14df-11f0-8f04-6c0b84df158f",
            "out_type": 1,
            "out_range": 2,
            "value": 2
        }]
    }],
    "est_time": 20
}

# 创建信号映射
signal_mapping = {
    "供电电压": "dspace_supply_voltage",
    "功耗电流": "dspace_power_current",
    "整车State状态": "dspace_vehicle_state",
    "总线报文发送标志位": "dspace_bus_message_flag",
    "PDCU唤醒原因": "dspace_pdcu_wake_reason",
    "整车模式": "dspace_vehicle_mode"
}

# 反向映射
reverse_mapping = {v: k for k, v in signal_mapping.items()}

# 测试模式
# 0: 正常模式，返回预期结果
# 1: 错误模式1，返回错误类型1的数据
# 2: 错误模式2，返回错误类型2的数据
# 3: 新状态模式，返回一组新的信号值
test_mode = 0

# 初始信号值设置
initial_signal_values = {
    "dspace_supply_voltage": 0,  # 供电电压初始值
    "dspace_power_current": 0.01,   # 功耗电流初始值
    "dspace_vehicle_state": 0,     # 整车State状态初始值
    "dspace_bus_message_flag": 0,  # 总线报文发送标志位初始值
    "dspace_pdcu_wake_reason": 0,  # PDCU唤醒原因初始值
    "dspace_vehicle_mode": 0       # 整车模式初始值
}
# 复位
@app.route('/api/v1/reset', methods=['POST'])
def reset():

    return jsonify(mock_data["ok"])
@app.route('/api/v1/send', methods=['POST'])
def send_signal():
    """
    处理发送信号请求
    """
    try:
        data = request.json
        print(f"接收到发送信号请求: {json.dumps(data, ensure_ascii=False)}")
        
        # 更新信号值
        for item in data:
            signal = item.get('signal')
            value = item.get('val')
            signal_values[signal] = value
            
            # 如果是供电电压，根据其值设置其他信号的值
            if reverse_mapping.get(signal) == "供电电压":
                # 根据测试模式设置其他信号的值
                set_other_signals_by_mode(test_mode)
        
        return jsonify({
            "ok": 1,
            "msg": "信号发送成功",
            "data": {}
        })
    except Exception as e:
        print(f"发送信号失败: {str(e)}")
        return jsonify({
            "ok": 0,
            "msg": f"信号发送失败: {str(e)}",
            "data": {}
        }), 500

@app.route('/api/v1/read', methods=['POST'])
def read_signal():
    """
    处理读取信号请求
    """
    try:
        data = request.json
        signals = data.get('signals', [])
        print(f"接收到读取信号请求: {json.dumps(data, ensure_ascii=False)}")

        global num
        if num == 0:
            pass
        else:
            set_other_signals_by_mode(0)
        num += 1
        if num == 2:
            num = 0
        # 获取信号值
        result = {}
        for signal in signals:
            result[signal] = signal_values.get(signal, 0.0)
        
        print(f"返回信号值: {json.dumps(result, ensure_ascii=False)}")
        return jsonify({
            "ok": 1,
            "msg": "信号读取成功",
            "data": result
        })
    except Exception as e:
        print(f"读取信号失败: {str(e)}")
        return jsonify({
            "ok": 0,
            "msg": f"信号读取失败: {str(e)}",
            "data": {}
        }), 500

@app.route('/api/v1/set_mode', methods=['POST'])
def set_mode():
    """
    设置测试模式
    """
    global test_mode
    try:
        data = request.json
        mode = data.get('mode', 0)
        if mode in [0, 1, 2, 3]:  # 添加模式3
            test_mode = mode
            set_other_signals_by_mode(test_mode)
            return jsonify({
                "ok": 1,
                "msg": f"测试模式已设置为: {mode}",
                "data": {"mode": mode}
            })
        else:
            return jsonify({
                "ok": 0,
                "msg": f"无效的测试模式: {mode}，有效值为 0, 1, 2, 3",  # 更新错误消息
                "data": {}
            }), 400
    except Exception as e:
        return jsonify({
            "ok": 0,
            "msg": f"设置测试模式失败: {str(e)}",
            "data": {}
        }), 500

def set_other_signals_by_mode(mode):
    """
    根据测试模式设置其他信号的值
    
    Args:
        mode: 测试模式
            0: 正常模式，返回预期结果
            1: 错误模式1，返回错误类型1的数据
            2: 错误模式2，返回错误类型2的数据
            3: 新状态模式，返回一组新的信号值
    """
    if mode == 0:
        # 正常模式，设置预期结果
        for item in test_data["expected_results"]:
            signal_name = signal_mapping.get(item["name"])
            if signal_name:
                signal_values[signal_name] = float(item["value"])
    elif mode == 1:
        # 错误模式1
        for item in test_data["error"][0]["out_data"]:
            signal_name = signal_mapping.get(item["name"])
            if signal_name:
                signal_values[signal_name] = float(item["value"])
        
        # 对于错误模式1中未指定的信号，使用预期结果
        for item in test_data["expected_results"]:
            signal_name = signal_mapping.get(item["name"])
            if signal_name and signal_name not in signal_values:
                signal_values[signal_name] = float(item["value"])
    elif mode == 2:
        # 错误模式2
        for item in test_data["error"][1]["out_data"]:
            signal_name = signal_mapping.get(item["name"])
            if signal_name:
                signal_values[signal_name] = float(item["value"])
    elif mode == 3:
        # 新状态模式 - 设置一组离谱的信号值
        # 这些值既不是预期结果，也不是已知的错误类型，而且非常离谱
        new_state_values = {
            "dspace_supply_voltage": 999.9,        # 供电电压 - 极端高值
            "dspace_power_current": 88.88,         # 功耗电流 - 极端高值
            "dspace_vehicle_state": 999,           # 整车State状态 - 不合理的高值
            "dspace_bus_message_flag": 255,        # 总线报文发送标志位 - 不合理的高值
            "dspace_pdcu_wake_reason": 127,        # PDCU唤醒原因 - 不合理的高值
            "dspace_vehicle_mode": 65535           # 整车模式 - 不合理的高值
        }
        
        # 更新信号值
        for signal, value in new_state_values.items():
            signal_values[signal] = value

@app.route('/', methods=['GET'])
def index():
    """
    首页，显示当前信号值和测试模式
    """
    return jsonify({
        "status": "running",
        "test_mode": test_mode,
        "signal_values": signal_values,
        "signal_mapping": signal_mapping
    })

if __name__ == '__main__':
    # 初始化信号值
    for signal, value in initial_signal_values.items():
        signal_values[signal] = value
    
    print(f"模拟API服务器已启动，测试模式: {test_mode}")
    print(f"信号映射: {json.dumps(signal_mapping, ensure_ascii=False, indent=2)}")
    print(f"初始信号值: {json.dumps(signal_values, ensure_ascii=False, indent=2)}")
    
    app.run(host='127.0.0.1', port=8080, debug=True)