#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 ResultJudge 类的功能
"""

import os
import json
import logging
import sys
from app.services.result_judge import ResultJudge

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_result_judge')

# 添加配置类
class Config:
    TEST_PALTFORM_URL = "http://localhost:8080"
    # SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:12345678@localhost:3306/test?charset=utf8"
    
    def get(self, key, default=None):
        """
        模拟字典的get方法，用于获取配置值
        """
        return getattr(self, key, default)

def create_mock_test_data():
    """
    创建模拟测试数据
    
    Returns:
        Dict: 模拟测试数据
    """
    return {
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

def create_signal_mapping():
    """
    创建信号映射文件
    
    Returns:
        str: 映射文件路径
    """
    mapping = {
        #"供电电压": "dspace_supply_voltage",
        "功耗电流": "dspace_power_current",
        "整车State状态": "dspace_vehicle_state",
        "总线报文发送标志位": "dspace_bus_message_flag",
        "PDCU唤醒原因": "dspace_pdcu_wake_reason",
        "整车模式": "dspace_vehicle_mode"
    }
    
    mapping_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "services", "signal_mapping.json")
    os.makedirs(os.path.dirname(mapping_path), exist_ok=True)
    
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    return mapping_path

def test_process_test_data(result_judge, test_data):
    """
    测试处理测试数据功能
    
    Args:
        result_judge: ResultJudge实例
        test_data: 测试数据
    """
    logger.info("测试处理测试数据功能")
    result = result_judge.process_test_data(test_data)
    logger.info(f"处理结果: {json.dumps(result, ensure_ascii=False)}")
    return result

def test_send_signal(result_judge, signal_data):
    """
    测试发送信号功能
    
    Args:
        result_judge: ResultJudge实例
        signal_data: 信号数据
    """
    logger.info("测试发送信号功能")
    result = result_judge.send_signal(signal_data)
    logger.info(f"发送结果: {json.dumps(result, ensure_ascii=False)}")
    return result

def test_get_test_result(result_judge):
    """
    测试获取测试结果功能
    
    Args:
        result_judge: ResultJudge实例
    """
    logger.info("测试获取测试结果功能")
    result = result_judge._get_test_result()
    logger.info(f"获取结果: {json.dumps(result, ensure_ascii=False)}")
    return result

def test_judge_test_result(result_judge, test_data):
    """
    测试判断测试结果功能
    
    Args:
        result_judge: ResultJudge实例
        test_data: 测试数据
    """
    logger.info("测试判断测试结果功能")
    result = result_judge.judge_test_result(test_data)
    logger.info(f"判断结果: {json.dumps(result, ensure_ascii=False)}")
    return result

def main():
    """
    主函数
    """
    logger.info("开始测试 ResultJudge 类的功能")
    
    # 创建信号映射文件
    mapping_path = create_signal_mapping()
    logger.info(f"信号映射文件已创建: {mapping_path}")
    
    # 创建模拟测试数据
    test_data = create_mock_test_data()
    logger.info(f"模拟测试数据已创建: {json.dumps(test_data, ensure_ascii=False)}")
    
    # 创建 ResultJudge 实例
    config = Config()  # 创建配置实例
    
    result_judge = ResultJudge(logger, config, round_id = 1)
    logger.info("ResultJudge 实例已创建")
    
    # 测试各个功能
    try:
        # 测试发送信号功能
        send_result = test_send_signal(result_judge, test_data["in_data"])
        
        # 测试获取测试结果功能
        get_result = test_get_test_result(result_judge)
        
        # 测试判断测试结果功能
        judge_result = test_judge_test_result(result_judge, test_data)
        
        # 测试处理测试数据功能
        #process_result = test_process_test_data(result_judge, test_data)
        
        logger.info("测试完成")
        
        # 输出测试结果摘要
        logger.info("测试结果摘要:")
        logger.info(f"发送信号: {'成功' if send_result.get('ok') == 1 else '失败'}")
        logger.info(f"获取测试结果: {'成功' if get_result.get('status') == 'success' else '失败'}")
        logger.info(f"判断测试结果: {'成功' if judge_result.get('strategy') is not None else '失败'}")
        logger.info(f"处理测试数据: {'成功' if process_result.get('strategy') is not None else '失败'}")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main()