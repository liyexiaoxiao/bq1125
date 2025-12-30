#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试结果判断模块
根据流程图实现测试结果的判断逻辑，处理example.json数据并调用API
"""

import os
import json
import requests
import time
import uuid
from typing import Dict, List, Any, Union, Optional
from .database_handler import TestResultHandler
from .bq_api import *


# 配置日志


class ResultJudge:
    """测试结果判断模块"""

    def __init__(self, logger, config, round_id, app=None):
        """
        初始化结果判断模块

        Args:
            config_path: 配置文件路径，可选
            api_base_url: API基础URL
        """
        self.app = app
        self.logger = logger
        self.config = config
        api_base_url = self.config.TEST_PALTFORM_URL
        db_url = self.config.SQLALCHEMY_DATABASE_URI
        # self.api_base_url = api_base_url
        self.round_id = round_id
        # self.send_api = f"{self.api_base_url}/api/v1/send"
        # self.read_api = f"{self.api_base_url}/api/v1/read"  # 添加读取API的URL
        # self.map_api = f"{self.api_base_url}/api/v1/mapping"  # 添加读取API的URL
        # self.reset_api = f"{self.api_base_url}/api/v1/reset"  # 添加读取API的URL

        # 初始化其他必要的变量
        self.test_results = {}
        self.signal_mapping = self._load_signal_mapping()

        # 读取信号的间隔时间(毫秒)，默认为100ms
        self.read_interval = self.config.READ_INTERVAL / 1000.0

        # 信号波动容差值，默认为0.1（10%）
        self.signal_tolerance = self.config.SIGNAL_TOLERANCE

        # 反向信号映射（从mapping插件变量名到信号名称）
        self.reverse_mapping = {v: k for k, v in self.signal_mapping.items()}

        # 测试运行次数
        self.test_times = 0

        # 数据库连接地址
        self.db_url = db_url

        # 数据库插入数据后的ID
        self.run_id = 0
        # 最近一次触发分析的 run_id，避免重复分析
        self.last_analyzed_run_id = 0

        # 本次处理策略
        self.new_processing_strategy = 0
        self.stop_signal = False

        # 初始信号值
        self.initial_signal_values = {}

    def _load_signal_mapping(self) -> Dict[str, str]:
        """
        加载信号映射关系

        Returns:
            Dict: 信号名称到mapping插件变量名的映射
        """
        # 实际应用中，这可能从配置文件或数据库加载
        # 这里简单示例，实际使用时需要替换为真实的映射关系
        mapping_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signal_mapping.json")
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    # def process_test_data(self, test_data_path: str) -> Dict[str, Any]:
    def process_test_data(self, test_data_in: Dict[str, bytes]) -> Dict[str, Any]:
        # def process_test_data(self, test_data_in: Dict[str, bytes]):
        """
        处理测试数据并执行测试

        Args:
            test_data_path: 测试数据文件路径

        Returns:
            Dict: 处理结果
        """
        try:
            # 加载测试数据(读取文件处理方式)
            # with open(test_data_path, 'r', encoding='utf-8') as f:

            # 处理单引号字符为双引号字符
            fixed_json = str(test_data_in).replace("'", '"')
            fixed_json = fixed_json.replace("None", 'null')
            # fixed_json = re.sub(r'\bNone\b', 'null', fixed_json)
            test_data = json.loads(fixed_json)

            # 开始处理测试流程
            return self.judge_test_result(test_data)
        except Exception as e:
            self.logger.error(f"处理测试数据时发生错误: {str(e)}")
            return {"status": "error", "message": f"处理测试数据时发生错误: {str(e)}"}

    def ensure_list(self, param):
        if isinstance(param, list):
            return param
        else:
            return [param]

    def send_signal(self, signal_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        发送信号到API

        Args:
            signal_data: 信号数据列表

        Returns:
            Dict: API响应
        """
        return send_api(self, signal_data)

    def judge_test_result(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        判断测试结果

        Args:
            test_data: 测试数据

        Returns:
            Dict: 判断结果，包含strategy、stop_signal和in_data
        """
        self.logger.info("开始判断测试结果")

        # 每次运行策略初始化为0
        self.new_processing_strategy = 0
        self.stop_signal = False

        # 初始化数据库单元
        db = TestResultHandler(self.logger, self.db_url)

        # 错误
        err = None
        # 获取输入数据
        in_data = test_data.get("in_data", [])

        # 主流程开始
        try:
            # 测试次数加1
            self.test_times += 1
            # 保存预期结果，供后续使用
            self.expected_results = test_data.get("expected_results", [])

            # 先读取当前系统中的信号并保存
            self.logger.info("读取当前系统中的信号作为基准值")
            initial_signals = self._get_test_result()
            if initial_signals.get("status") != "success":
                self.logger.error(f"读取初始信号失败: {initial_signals.get('message')}")
                err = 1
                return {"strategy": -1, "stop_signal": True, "in_data": in_data}
            """
            # 保存初始信号值，供后续比较使用
            self.initial_signal_values = {
                item.get("uuid"): item.get("value") 
                for item in initial_signals.get("data", [])
            }
            """
            # 自定义初始信号值，不再从系统读取
            self.initial_signal_values = {
                "630c86f7-14dd-11f0-ad8e-6c0b84df158f": 0.01,  # 功耗电流初始值
                "35695f8f-14dd-11f0-a9e0-6c0b84df158f": 0,  # 整车State状态初始值
                "b0bf7c0b-14dd-11f0-a72f-6c0b84df158f": 0,  # 总线报文发送标志位初始值
                "c8391a2f-14dd-11f0-b145-6c0b84df158f": 0,  # PDCU唤醒原因初始值
                "14b7c71b-14df-11f0-8f04-6c0b84df158f": 0  # 整车模式初始值
            }
            self.logger.info(f"初始信号值: {json.dumps(self.initial_signal_values, ensure_ascii=False)}")

            # 发送输入信号
            if not in_data:
                err = 1
                return {"strategy": -1, "stop_signal": True, "in_data": in_data}
            # 发送输入信号
            send_result = self.send_signal(in_data)
            # if '未找到路由' in send_result['error'].values():
            #     return {"strategy": 0, "stop_signal": False, "in_data": in_data}
            if send_result.get("ok") != 1:
                err = 1
                return {"strategy": -1, "stop_signal": True, "in_data": in_data}

            # 在预期时间内每隔read_interval读取一次信号
            # est_time = test_data.get("est_time", 5)
            est_time = 20
            self.logger.info(f"预期时间: {est_time}秒，每隔{self.read_interval}秒读取一次信号")

            start_time = time.time()
            end_time = start_time + est_time
            last_read_time = start_time - self.read_interval  # 确保第一次循环就读取

            # 使用预期结果中的整车状态作为目标值，如果不存在则按轮次设置默认目标
            target_state = None
            for item in self.expected_results:
                if item.get("name") == "整车State状态":
                    target_state = item.get("value")
                    break
            if target_state is None:
                is_wakeup_round = self.test_times % 2
                target_state = 170 if is_wakeup_round == 1 else 30
                self.logger.info(f"未在预期结果中找到目标整车状态，按轮次使用默认值: {target_state}")
            else:
                self.logger.info(f"目标整车状态值来自预期结果: {target_state}")

            # 在预期时间内循环读取信号
            while time.time() < end_time:
                current_time = time.time()

                # 判断是否到达读取间隔
                if current_time - last_read_time >= self.read_interval:
                    # 读取信号
                    self.logger.info(f"读取信号，已过时间: {current_time - start_time:.2f}秒")
                    # 删除19秒
                    # time.sleep(19)
                    result = self._get_test_result()

                    # 检查结果是否异常
                    if self._is_result_abnormal(result):
                        # 异常结果处理 - 直接保存错误信息并判断是否继续测试
                        self._save_error_info(result)
                        if not self._should_continue_test(result):
                            self.logger.info("非预期异常，退出测试")
                            err = 1
                            return {"strategy": -1, "stop_signal": True, "in_data": in_data}
                    else:
                        # 检查整车状态是否达到目标值（根据轮次判断）
                        actual_data = result.get("data", [])
                        vehicle_state = None
                        for item in actual_data:
                            # 假设整车状态信号的UUID是"35695f8f-14dd-11f0-a9e0-6c0b84df158f"
                            if item.get("uuid") == "35695f8f-14dd-11f0-a9e0-6c0b84df158f":
                                vehicle_state = item.get("value")
                                break

                        if vehicle_state is not None and vehicle_state == target_state:
                            self.logger.info(
                                f"{'唤醒轮' if is_wakeup_round else '休眠轮'}测试通过，整车状态达到目标值: {target_state}")
                            # 保存结果到数据库
                            current_time = time.time() # 重新取现在的时间
                            self.run_id = db.store_test_result(
                                (current_time - start_time) * 1000,
                                test_data=test_data,
                                result_data=result,
                                strategy=0,  # 测试通过策略为0
                                round_id=self.round_id
                            )
                            
                            print(f"数值插入成功，run_id: {self.run_id}，整车状态值：{vehicle_state}，耗时：{current_time - start_time:.2f}")
                            self.logger.info(f"数据插入成功，run_id: {self.run_id}")
                            return {"strategy": 0, "stop_signal": False, "in_data": in_data}

                    # 更新上次读取时间
                    last_read_time = current_time

                # 短暂休眠，避免CPU占用过高
                time.sleep(0.1)

            # 预期时间结束，如果没有得到明确结果，默认返回继续测试
            self.logger.info("预期时间结束，未得到明确结果，默认继续测试")

        except Exception as err:
            self.logger.error(f"测试结果判断过程中发生错误: {str(err.args[0])}")

        finally:

            if err is not None:
                return {"strategy": -1, "stop_signal": True, "in_data": in_data}

            if self.new_processing_strategy == 0:
                if self.run_id and self.run_id % 20 == 0 and self.run_id != self.last_analyzed_run_id:
                    print(f"[DEBUG] 触发时间分析，当前 run_id: {self.run_id}")
                    self.last_analyzed_run_id = self.run_id
                    db = TestResultHandler(self.logger, self.db_url, app=self.app)
                    strategy = db.analyze_durations(self.run_id)
                    # print(f"分析结果：strategy={strategy}")
                    return {"strategy": strategy, "stop_signal": False, "in_data": in_data}
            if err is None:
                self.stop_signal = False
                return {"strategy": self.new_processing_strategy, "stop_signal": self.stop_signal, "in_data": in_data}

    def _get_test_result(self) -> Dict[str, Any]:
        """
        获取测试结果

        Returns:
            Dict: 测试结果
        """
        self.logger.info("获取测试结果")
        return read_api(self)
        # try:
        #     # 获取需要读取的信号列表
        #     signal_names = list(self.signal_mapping.values())
        #
        #     if not signal_names:
        #         self.logger.error("没有配置需要读取的信号")
        #         return {
        #             "status": "error",
        #             "message": "没有配置需要读取的信号",
        #             "timestamp": time.time()
        #         }
        #
        #     # 准备请求数据
        #     payload = {
        #         "signals": signal_names,
        #         "mode": 0
        #     }
        #
        #     # 发送请求
        #     response = requests.post(self.read_api, json=payload)
        #
        #     # 解析响应
        #     if response.status_code == 200:
        #         result = response.json()
        #         self.logger.info(f"API响应: {json.dumps(result, ensure_ascii=False)}")
        #
        #         if result.get("ok") == 1:
        #             # 处理读取结果
        #             processed_results = self._process_read_results(result.get("data", {}))
        #
        #             return {
        #                 "status": "success",
        #                 "timestamp": time.time(),
        #                 "data": processed_results
        #             }
        #         else:
        #             self.logger.error(f"读取信号失败: {result.get('msg')}")
        #             return {
        #                 "status": "error",
        #                 "message": f"读取信号失败: {result.get('msg')}",
        #                 "timestamp": time.time()
        #             }
        #     else:
        #         self.logger.error(f"API请求失败，状态码: {response.status_code}")
        #         return {
        #             "status": "error",
        #             "message": f"API请求失败，状态码: {response.status_code}",
        #             "timestamp": time.time()
        #         }
        #
        # except Exception as e:
        #     self.logger.error(f"获取测试结果时发生错误: {str(e)}")
        #     return {
        #         "status": "error",
        #         "message": f"获取测试结果时发生错误: {str(e)}",
        #         "timestamp": time.time()
        #     }

    def _process_read_results(self, result_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理读取的结果

        Args:
            result_data: 读取的结果数据

        Returns:
            List: 处理后的结果列表
        """
        processed_results = []

        # 将结果转换为测试结果格式 {'挡位信号': 1, '整车State状态': 49, '蓄电池剩余电量SOC': 0.0}
        for dspace_signal, value in result_data.items():
            # 获取原始信号名称
            original_signal = self.reverse_mapping.get(dspace_signal, dspace_signal)

            # if not original_signal:
            #     self.logger.warn(f"未找到信号 {dspace_signal} 的原始名称")
            #     continue

            # 查找对应的UUID
            uuid = None
            for item in self.expected_results:
                if item.get("name") == original_signal:
                    uuid = item.get("uuid")
                    break

            # if not uuid:
            #     self.logger.warn(f"未找到信号 {original_signal} 的UUID")
            #     continue

            # 添加到处理结果
            processed_results.append({
                "name": original_signal,
                "uuid": uuid,
                "value": value
            })

        return processed_results

    def _is_result_abnormal(self, result: Dict[str, Any]) -> bool:
        """
        判断结果是否异常

        Args:
            result: 测试结果

        Returns:
            bool: 是否异常
        """
        self.logger.info("判断结果是否异常")
        # 根据实际情况判断结果是否异常
        return result.get("status") != "success" or not result.get("data")

    def _is_expected_exception(self, result: Dict[str, Any], test_data: Dict[str, Any]) -> bool:
        """
        判断是否是预期异常

        Args:
            result: 测试结果
            test_data: 测试数据

        Returns:
            bool: 是否是预期异常
        """
        self.logger.info("判断是否是预期异常")
        # 使用error字段而不是expected_exceptions
        errors = test_data.get("error", [])
        exception_type = result.get("exception_type")

        # 检查异常类型是否在任何error的error_type中
        for error in errors:
            if error.get("error_type") == exception_type:
                return True

        return False

    def _process_expected_exception(self, result: Dict[str, Any], test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理预期异常

        Args:
            result: 测试结果
            test_data: 测试数据

        Returns:
            Dict: 处理结果
        """
        self.logger.info("处理预期异常")
        # 处理预期异常
        return {"status": "success", "message": "预期异常，测试通过", "data": result}

    def _save_error_info(self, result: Dict[str, Any]) -> None:
        """
        保存错误信息

        Args:
            result: 错误信息
        """
        self.logger.error("保存错误信息")
        # 保存错误信息到日志或数据库
        error_info = {
            "error_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "data": result
        }
        self.logger.error(error_info)
        # error_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "errors", f"error_{error_info['error_id']}.json")
        # os.makedirs(os.path.dirname(error_file), exist_ok=True)
        # with open(error_file, 'w', encoding='utf-8') as f:
        #     json.dump(error_info, f, ensure_ascii=False, indent=2)
        self.logger.error(f"错误信息已保存: {error_info}")

    def _should_continue_test(self, result: Dict[str, Any]) -> bool:
        """
        判断是否需要继续测试

        Args:
            result: 测试结果

        Returns:
            bool: 是否继续测试
        """
        self.logger.info("判断是否需要继续测试")
        # 根据错误严重程度判断是否继续测试
        # 这里简单实现，实际可能需要更复杂的逻辑
        return not result.get("critical_error", False)

    def _compare_results(self, actual_result: Dict[str, Any], expected_results: List[Dict[str, Any]],
                         errors: List[Dict[str, Any]], in_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        比较预期结果和实际结果，并判断是否匹配预期结果、已知错误或新状态

        Args:
            actual_result: 实际结果
            expected_results: 预期结果列表
            errors: 已知错误列表
            in_data: 输入数据列表

        Returns:
            Dict: 比较结果，包含strategy和stop_signal
        """
        self.logger.info("比较预期结果和实际结果")

        # 提取实际结果数据
        actual_data = actual_result.get("data", [])
        actual_dict = {item.get("name"): item for item in actual_data}

        # 首先检查是否匹配预期结果
        expected_match = True
        mismatches = []

        for expected in expected_results:
            uuid = expected.get("name")
            if uuid not in actual_dict:
                expected_match = False
                mismatches.append({
                    "expected": expected,
                    "actual": None,
                    "reason": "缺少预期结果项"
                })
                continue

            actual = actual_dict[uuid]
            expected_value = expected.get("value")
            actual_value = actual.get("value")

            # 根据out_type和out_range判断比较方式
            out_type = expected.get("out_type")
            out_range = expected.get("out_range")

            # 阈值类型比较
            if out_type == 1:  # 阈值类型
                if out_range == 1:  # 大于等于
                    if not (actual_value >= expected_value):
                        expected_match = False
                        mismatches.append({
                            "expected": expected,
                            "actual": actual,
                            "reason": f"值不满足大于等于条件: 预期 >= {expected_value}, 实际 {actual_value}"
                        })
                elif out_range == 2:  # 等于
                    if not (actual_value == expected_value):
                        expected_match = False
                        mismatches.append({
                            "expected": expected,
                            "actual": actual,
                            "reason": f"值不相等: 预期 = {expected_value}, 实际 {actual_value}"
                        })
                elif out_range == 3:  # 小于等于
                    if not (actual_value <= expected_value):
                        expected_match = False
                        mismatches.append({
                            "expected": expected,
                            "actual": actual,
                            "reason": f"值不满足小于等于条件: 预期 <= {expected_value}, 实际 {actual_value}"
                        })
            else:
                # 默认使用相等比较
                if expected_value != actual_value:
                    expected_match = False
                    mismatches.append({
                        "expected": expected,
                        "actual": actual,
                        "reason": f"值不匹配: 预期 {expected_value}, 实际 {actual_value}"
                    })

        # 如果匹配预期结果，直接返回成功
        if expected_match:
            self.logger.info("测试结果与预期匹配")
            return {
                "match_type": "expected",
                "strategy": 0,
                "stop_signal": False,
                "match": True,
                "mismatches": [],
                "expected": expected_results,
                "actual": actual_data
            }

        # 如果不匹配预期结果，检查是否匹配已知错误
        for error in errors:
            error_type = error.get("error_type")
            out_data = error.get("out_data", [])

            # 检查是否匹配当前错误类型
            error_match = True
            for expected in out_data:
                uuid = expected.get("uuid")
                if uuid not in actual_dict:
                    error_match = False
                    break

                actual = actual_dict[uuid]
                expected_value = expected.get("value")
                actual_value = actual.get("value")

                # 根据out_type和out_range判断比较方式
                out_type = expected.get("out_type")
                out_range = expected.get("out_range")

                # 阈值类型比较
                if out_type == 1:  # 阈值类型
                    if out_range == 1:  # 大于等于
                        if not (actual_value >= expected_value):
                            error_match = False
                            break
                    elif out_range == 2:  # 等于
                        if not (actual_value == expected_value):
                            error_match = False
                            break
                    elif out_range == 3:  # 小于等于
                        if not (actual_value <= expected_value):
                            error_match = False
                            break
                else:
                    # 默认使用相等比较
                    if expected_value != actual_value:
                        error_match = False
                        break

            if error_match:
                self.logger.info(f"匹配到已知错误类型: {error_type}")
                # 如果是卡住情况（error_type为2）或者error_type为1，设置特殊返回值
                if error_type == 1:
                    return {
                        "match_type": "error",
                        "error_type": error_type,
                        "strategy": -2,
                        "stop_signal": True,
                        "match": False,
                        "mismatches": mismatches,
                        "expected": expected_results,
                        "actual": actual_data
                    }
                elif error_type == 2:
                    return {
                        "match_type": "error",
                        "error_type": error_type,
                        "strategy": -3,
                        "stop_signal": True,
                        "match": False,
                        "mismatches": mismatches,
                        "expected": expected_results,
                        "actual": actual_data
                    }
                return {
                    "match_type": "error",
                    "error_type": error_type,
                    "strategy": 0,
                    "stop_signal": False,
                    "match": False,
                    "mismatches": mismatches,
                    "expected": expected_results,
                    "actual": actual_data
                }

        # 既不匹配预期结果也不匹配已知错误，检查是否与初始状态相近
        # 如果与初始状态相近，则认为没有发生实质性变化，不是新状态
        if self.initial_signal_values:
            is_similar_to_initial = True
            for item in actual_data:
                uuid = item.get("uuid")
                actual_value = item.get("value")

                # 如果初始状态中有该信号
                if uuid in self.initial_signal_values:
                    initial_value = self.initial_signal_values[uuid]

                    # 计算允许的波动范围
                    # 对于接近0的值，使用绝对容差
                    if abs(initial_value) < 0.001:
                        tolerance = 0.001
                    else:
                        # 对于非零值，使用相对容差
                        tolerance = abs(initial_value * self.signal_tolerance)

                    # 检查当前值是否在允许的波动范围内
                    if abs(actual_value - initial_value) > tolerance:
                        is_similar_to_initial = False
                        self.logger.info(
                            f"信号 {item.get('name')} 超出波动范围: 初始值 {initial_value}, 当前值 {actual_value}, 容差 {tolerance}")
                        break
                else:
                    # 初始状态中没有该信号，认为不相似
                    is_similar_to_initial = False
                    self.logger.info(f"初始状态中没有信号 {item.get('name')}")
                    break

            if is_similar_to_initial:
                self.logger.info("测试结果与初始状态相似，不认为是新状态")
                return {
                    "match_type": "similar_to_initial",
                    "strategy": 0,
                    "stop_signal": False,
                    "match": False,
                    "mismatches": mismatches,
                    "expected": expected_results,
                    "actual": actual_data
                }

        # 既不匹配预期结果、已知错误，也不与初始状态相似，根据输入参数数量返回不同策略
        self.logger.warn("既不匹配预期结果也不匹配已知错误，发现新状态！")

        # 获取输入参数数量
        # 获取输入参数数量
        if isinstance(in_data, list):
            strategy = 2  # 多参数
        else:
            strategy = 1  # 单参数
        in_data_count = len(in_data)

        self.logger.info(f"输入参数数量: {in_data_count}, 策略: {strategy}")

        return {
            "match_type": "new",
            "strategy": strategy,
            "stop_signal": False,
            "match": False,
            "mismatches": mismatches,
            "expected": expected_results,
            "actual": actual_data
        }

# def main():
#     """主函数，用于测试"""
#     # 创建结果判断模块实例
#     judge = ResultJudge()
#
#     # 测试数据文件路径
#     test_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.json")
#
#     # 处理测试数据
#     result = judge.process_test_data(test_data_path)
#     print(f"处理结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
#
# if __name__ == "__main__":
#     main()
