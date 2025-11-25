import random
import copy
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from itertools import product
from app.models.models import *
import os
import json
from .database_handler import TestResultHandler

'''
in_type 1--范围内取值 2--固定值
in_range  1--不包含边界值  2--固定值单值
out_type 1--阈值类型
out_range  1--大于等于 2--等于  3--小于等于
'''

class DataVariation:
    def __init__(self, logger, config, case_list: List[Dict[str, Any]]=None, app=None):
        self.logger = logger
        self.config = config
        self.original_cases = case_list
        '''用于处理cases'''
        self.expected_time_type1 = None
        self.expected_case_type1 = []
        self.error_time_type1 = None
        self.error_case_type1 = []
        self.stuck_case_type1 = []
        self.expected_time_type2 = None
        self.expected_case_type2 = []
        self.error_time_type2 = None
        self.error_case_type2 = []
        self.stuck_case_type2 = []
        ''''''
        self.data_pool = []
        self.current_case = {}
        self.app = app
        # 新增：单参数随机选择的参数池
        self.single_param_pool = []
        
    # ---------- 公共接口 ----------
    def generate_initial_variations(self) -> bool:
        """生成初始变异数据池"""
        run_times = self.config.RUN_TIMES
        mode = self.config.MODE

        self.data_pool = []  # 清空现有数据池
        self.classify_cases() # 预处理origin_cases，进行分类
        self.build_single_param_pool() # 建立单参数随机选择池
        # if not self.expected_case_type1 or not self.expected_case_type2:
        #     self.logger.error("分类后的 expected_case 为空，无法生成输入数据")
        #     return False
        
        if mode == "MIX":
            # 随机比例生成
            type1_count = int(run_times/2)
            type2_count = int(run_times/2)
            # while True:
            #     type1_percent = random.randint(40, 60)
            #     type2_percent = 100 - type1_percent
            #     if abs(type1_percent - type2_percent) <= 20:
            #         break
            # type1_count = int(run_times * type1_percent / 100)
            # type2_count = run_times - type1_count
        elif mode == "WAKE": # type1是单输入、是唤醒
            type1_count = run_times
            type2_count = 0
        elif mode == "SLEEP":
            type1_count = 0
            type2_count = run_times
        else:
            self.logger.error(f"未知的运行模式：{mode}")
            return False

        # 生成type1用例（随机选择不同参数）
        for _ in range(type1_count):
            # 随机选择一个参数进行唤醒测试
            if self.single_param_pool:
                # 从参数池中随机选择一个参数
                selected_param = random.choice(self.single_param_pool)
                in_put = selected_param["param_config"]
                expected_results = selected_param["expected_output"]
                error_info = selected_param["error_info"]
                stuck_info = selected_param["stuck_info"]
                print(in_put)
            else:
                # 回退到原始方法
                if not self.expected_case_type1:
                    continue
                idx = random.randint(0, len(self.expected_case_type1) - 1)
                original_case = self.expected_case_type1[idx]
                if type(original_case["in_put"]) == type([]):
                    continue
                in_put = original_case["in_put"]
                expected_results = original_case["out_put"]
                error_info = self.error_case_type1[idx].get("error", [])
                stuck_info = self.stuck_case_type1[idx].get("stuck", [])
                print(f"使用原始方法: {in_put}")
            
            '''新的 in_put 字段'''
            # 判断 in_put 的类型
            step_len = float(in_put.get("step_len", 1))
            if step_len.is_integer():
                data_type = "int"
            else:
                data_type = "float"
            # 调用 generate_value 来生成具体的 in_put 的 value
            in_put_value = self.generate_value(in_put)
            
            new_in_put = {
                "name": in_put.get("name"),
                "data_type": data_type,
                "value": in_put_value,
                "ID": in_put.get("uuid", "")
            }

            ''' 新的 error 字段'''
            new_error = [
                {"error_type": 1, "out_data": error_info},
                {"error_type": 2, "out_data": stuck_info}
            ]
            
            new_data = {
                "type": 1,
                "in_data": new_in_put,
                "expected_results": expected_results,
                "error": new_error,
                "est_time": self.expected_time_type1
            }
            
            # 将生成的数据添加到数据池
            self.data_pool.append(new_data)
        
        # 生成type2用例
        for _ in range(type2_count):
            idx = random.randint(0, len(self.expected_case_type2) - 1)
            original_case = self.expected_case_type2[idx]
            in_put_list = original_case["in_put"]
            if type(original_case["in_put"]) == type({}):
                continue
            expected_results = original_case["out_put"]
            '''新的 in_put 字段'''
            new_in_put = []
            for in_put in in_put_list:
                step_len = float(in_put.get("step_len", 1))
                if step_len.is_integer():
                    data_type = "int"
                else:
                    data_type = "float"

                in_put_value = self.generate_value(in_put)

                new_in_put_ele = {
                    "name": in_put.get("name"),
                    "data_type": data_type,
                    "value": in_put_value,
                    "ID": ""
                }
                new_in_put.append(new_in_put_ele)

            ''' 新的 error 字段'''
            error_entry = self.error_case_type2[idx].get("error")
            stuck_entry = self.stuck_case_type2[idx].get("stuck")
            new_error = [
                {"error_type": 1, "out_data": error_entry},
                {"error_type": 2, "out_data": stuck_entry}
            ]
            
            new_data = {
                "type": 2,
                "in_data": new_in_put,
                "expected_results": expected_results,
                "error": new_error,
                "est_time": self.expected_time_type1
            }
            
            # 将生成的数据添加到数据池
            self.data_pool.append(new_data)

        if mode == "MIX":
            n = len(self.data_pool)
            mid = n // 2
            first_half = self.data_pool[:mid]
            second_half = self.data_pool[mid:]
            result = []
            for i in range(mid):
                result.append(first_half[i])
                result.append(second_half[i])
            self.data_pool = result
            # random.shuffle(self.data_pool)
        # 可以在output.json看生成的用例数据
        #with open("output.json", "w", encoding="utf-8") as f:
             #json.dump(self.data_pool, f, ensure_ascii=False, indent=4)

        return True

    def pop_first_data(self) -> Optional[Dict[str, Any]]:
        """获取并删除 data_pool 中的第一个数据"""
        if self.data_pool:
            self.current_case = self.data_pool[0]
            return self.data_pool.pop(0)
        else:
            if self.data_pool is []:
                self.logger.info("数据池为空，无法弹出数据")
                return None
            else:
                self.logger.error("数据池弹出操作异常")
                return None

    def trigger_variation(self, response: Dict[str, Any]) -> Optional[bool]:
        """根据返回结果决定是否继续变异并调用对应策略的变异函数。"""
        # stop_signal = response.get("stop_signal")
        strategy = response.get("strategy")

        # if stop_signal:
        #     print("stop")

        if strategy == 0:
            self.pop_first_data()

        elif strategy == 1:
            self.generate_single_param()

        elif strategy == 2:
            self.generate_multi_param()

        elif strategy == 3:
            self.generate_repeat_execution()

    def based_new_state_fuzz(self, round_id):
        """基于新状态发生变异，向数据池中插入数据。"""
        # 数据库中查询上一轮所有新状态数据
        self.data_pool = []
        db_handler = TestResultHandler(self.logger, db_url=self.config.SQLALCHEMY_DATABASE_URI, app=self.app)
        datalist = db_handler.get_new_status_by_round(round_id)
        if datalist is None:
            self.logger.error("未发现上一轮有新状态，测试停止")
            return False
        for i in datalist:
            current_case = {"type": 0, "in_data": [], 'expected_results': [], 'error': [], 'est_time': 0}
            current_case["type"] = i["type"]
            current_case["in_data"] = eval(i["actual_input"])
            current_case["expected_results"] = eval(i["expected_output"])

            expected_error_output =eval(i["expected_error_output"])
            if len(expected_error_output) != 0:
                expected_error_output_dict = expected_error_output[0]
            else:
                expected_error_output_dict = {}

            expected_stuck_output = eval(i["expected_stuck_output"])
            if len(expected_stuck_output) != 0:
                expected_stuck_output_dict = expected_stuck_output[0]
            else:
                expected_stuck_output_dict = {}

            current_case["error"] = [expected_error_output_dict, expected_stuck_output_dict]
            current_case["est_time"] = i["expected_duration"]
            # 输入第一条用例
            self.current_case = current_case
            # 变异数据生成加入数据池
            strategy = i["strategy"]
            if strategy == 1:
                self.generate_single_param()

            elif strategy == 2:
                self.generate_multi_param()

            elif strategy == 3:
                self.generate_repeat_execution()
        return True


    # ---------- 变异策略实现 ----------
    def generate_single_param(self) -> None:
        """单参数变异策略：生成邻近值的变异用例并插入数据池前端"""
        variation_time = self.config.SINGLE_VARIATION_TIME
        current_case = copy.deepcopy(self.current_case)
        if not current_case:
            self.logger.error("当前用例不存在，无法进行单参数变异")
            return

        # 判断是单参数还是多参数用例
        if not isinstance(current_case["in_data"], dict):
            self.logger.error("当前用例为多参数，无法进行单参数变异")
            return

        param = current_case["in_data"]
        case_type = current_case["type"]
        mutated_cases = []

        # 获取原始参数配置
        original_config = self.find_original_param_config(param["name"], case_type)
        if not original_config:
            self.logger.error("找不到原始配置，无法进行单参数变异")
            return

        # 获取可能的值范围
        possible_values = self.get_param_values(original_config)
        if not possible_values:  # 空值保护
            self.logger.error(f"参数{param['name']}的可能值列表为空")
            return

        # 处理固定值情况
        if len(possible_values) == 1:
            for _ in range(variation_time):
                new_case = copy.deepcopy(current_case)
                new_case["in_data"]["value"] = possible_values[0]
                self.regenerate_case_metadata(new_case, original_config)
                mutated_cases.append(new_case)
            self.data_pool[0:0] = mutated_cases  # 批量插入前端
            return

        try:
            current_value = float(param["value"])
            idx = possible_values.index(current_value)

            neighbor_values = []
            window_radius = 0
            max_radius = max(idx, len(possible_values) - idx - 1)

            # 螺旋式滑动窗口算法
            while len(neighbor_values) < variation_time and window_radius <= max_radius:
                # 向左扩展
                if idx - window_radius >= 0:
                    neighbor_values.append(possible_values[idx - window_radius])
                # 向右扩展（避免radius=0时重复添加当前值）
                if window_radius != 0 and idx + window_radius < len(possible_values):
                    neighbor_values.append(possible_values[idx + window_radius])
                window_radius += 1

            # 去重并排除当前值
            neighbor_values = [v for v in list(set(neighbor_values)) if v != current_value]

            # 保底机制：如果无可用值则回退全量值（包含当前值）
            if not neighbor_values:
                neighbor_values = possible_values.copy() + [current_value]

        except ValueError:
            self.logger.error(f"单参数变异数值错误，当前值{current_value}不在可能值范围内")
            return

        # 生成10个值
        neighbor_values = random.choices(neighbor_values, k=variation_time)

        # 生成变异用例
        for new_value in neighbor_values:
            new_case = copy.deepcopy(current_case)
            new_case["in_data"]["value"] = new_value
            self.regenerate_case_metadata(new_case, original_config)
            mutated_cases.append(new_case)

        # 插入数据池前端
        self.data_pool[0:0] = mutated_cases

    def generate_multi_param(self) -> None:
        """多参数变异策略：生成邻近值的变异用例并插入数据池前端"""
        variation_time = self.config.MULTIPLE_VARIATION_TIME
        current_case = copy.deepcopy(self.current_case)
        if not current_case:
            self.logger.error("当前用例不存在，无法进行多参数变异策略2")
            return

        # 判断是多参数用例
        is_multi_param = isinstance(current_case["in_data"], list)
        if not is_multi_param:
            self.logger.error("当前用例为单参数，无法进行多参数变异")
            return
        params = current_case["in_data"]
        type = current_case["type"]

        # 存储所有可能的变异组合
        mutated_cases = []

        # 为每个参数准备邻近值列表
        param_neighbors = {}
        for param in params:
            # 获取原始参数配置
            original_config = self.find_original_param_config(param["ID"], type)
            if not original_config:
                continue

            # 获取可能的值范围
            possible_values = self.get_param_values(original_config)
            if not possible_values:  # 空值保护
                self.logger.error(f"参数{param['name']}的可能值列表为空")
                continue

            # 固定值直接处理（包括单值情况）
            if len(possible_values) == 1:
                param_neighbors[param["ID"]] = possible_values.copy()
                continue

            try:
                current_value = float(param["value"])
                idx = possible_values.index(current_value)

                neighbor_values = []
                window_radius = 0
                max_radius = max(idx, len(possible_values) - idx - 1)

                # 螺旋式滑动窗口算法
                while len(neighbor_values) < variation_time and window_radius <= max_radius:
                    # 向左扩展
                    if idx - window_radius >= 0:
                        neighbor_values.append(possible_values[idx - window_radius])
                    # 向右扩展
                    if idx + window_radius < len(possible_values) and window_radius != 0:
                        neighbor_values.append(possible_values[idx + window_radius])
                    window_radius += 1

                # 移除当前值并去重
                neighbor_values = [v for v in list(set(neighbor_values)) if v != current_value]

                # 保底逻辑：如果全部排除则使用全部可能值
                if not neighbor_values:
                    neighbor_values = possible_values.copy()

                # 最终采样
                param_neighbors[param["ID"]] = random.choices(neighbor_values, k=variation_time)

            except ValueError:
                self.logger.error(f"多参数变异数值错误，参数{param['name']}的当前值{current_value}不在可能值范围内")
                continue

        # 如果没有有效的参数可以变异，直接返回
        if not param_neighbors:
            self.logger.error("没有有效的参数可以进行变异")
            return

        # 生成变异用例组合
        for _ in range(variation_time):  # 生成10个变异组合
            new_case = copy.deepcopy(current_case)
            modified = False

            # 对每个参数随机选择是否变异(50%概率)
            for param in new_case["in_data"]:
                if param["ID"] in param_neighbors and random.random() < 0.5:
                    # 随机选择一个邻近值
                    new_value = random.choice(param_neighbors[param["ID"]])
                    param["value"] = str(new_value) if param["data_type"] == "float" else str(int(new_value))
                    modified = True

            # 如果至少修改了一个参数，则添加到变异用例列表
            if modified:
                # 获取第一个修改参数的原始配置用于重新生成元数据
                for param in new_case["in_data"]:
                    if "value" in param and param["value"] != current_case["in_data"][0]["value"]:
                        original_config = self.find_original_param_config(param["ID"], type)
                        if original_config:
                            self.regenerate_case_metadata(new_case, original_config)
                            break

                mutated_cases.append(new_case)

        # 将新用例插入数据池前端
        for case in reversed(mutated_cases):
            self.data_pool.insert(0, case)
        print(self.data_pool)

    def generate_repeat_execution(self) -> None:
        """多参数变异-3：向列表前端添加若干与实际异常数据重复的数据"""
        variation_time = self.config.REPEAT_VARIATION_TIME
        if not self.current_case:
            self.logger.error("当前用例不存在，无法进行多参数变异策略3")
            return

        # 直接复制原始用例指定次数并添加到前端
        for _ in range(variation_time):
            self.data_pool.insert(0, copy.deepcopy(self.current_case))

    # ---------- 辅助方法 ----------
    def build_single_param_pool(self) -> None:
        """建立单参数随机选择池，包含所有可用于唤醒测试的参数"""
        self.single_param_pool = []
        
        # 1. 添加原有的单参数用例（如CC2电压）
        for case in self.expected_case_type1:
            in_put = case.get("in_put")
            if isinstance(in_put, dict):
                # 查找对应的错误和卡顿信息
                error_info = []
                stuck_info = []
                
                # 在error_case_type1中查找对应的信息
                for error_case in self.error_case_type1:
                    error_in_put = error_case.get("in_put")
                    if isinstance(error_in_put, dict) and error_in_put.get("uuid") == in_put.get("uuid"):
                        error_info = error_case.get("error", [])
                        break
                
                # 在stuck_case_type1中查找对应的信息
                for stuck_case in self.stuck_case_type1:
                    stuck_in_put = stuck_case.get("in_put")
                    if isinstance(stuck_in_put, dict) and stuck_in_put.get("uuid") == in_put.get("uuid"):
                        stuck_info = stuck_case.get("stuck", [])
                        break
                
                param_entry = {
                    "param_config": in_put,
                    "expected_output": case.get("out_put", []),
                    "error_info": error_info,
                    "stuck_info": stuck_info,
                    "source": "type1_original"
                }
                self.single_param_pool.append(param_entry)
        
        # 2. 从专门的单参数唤醒测试配置文件中加载标准配置
        wake_config_file = os.path.join(self.config.DATA_DIR, "assert_001.json")
        try:
            with open(wake_config_file, 'r', encoding='utf-8') as f:
                wake_config_data = json.load(f)
                
            # 遍历专门的单参数唤醒测试配置
            for wake_case in wake_config_data.get("value", []):
                in_put = wake_case.get("in_put")
                if isinstance(in_put, dict):
                    # 检查是否已经在参数池中（避免重复）
                    param_uuid = in_put.get("uuid")
                    if not any(p["param_config"].get("uuid") == param_uuid for p in self.single_param_pool):
                        
                        param_entry = {
                            "param_config": in_put,                        # 使用标准的参数配置
                            "expected_output": wake_case.get("out_put", []), # 使用对应的预期输出
                            "error_info": wake_case.get("error", []),      # 使用对应的错误预期
                            "stuck_info": wake_case.get("stuck", []),      # 使用对应的卡顿预期
                            "source": "wake_config_standard"               # 标记来源
                        }
                        self.single_param_pool.append(param_entry)
                        
            self.logger.info(f"从标准唤醒配置文件加载了 {len([p for p in self.single_param_pool if p['source'] == 'wake_config_standard'])} 个参数")
            
        except FileNotFoundError:
            self.logger.warning(f"未找到标准唤醒配置文件: {wake_config_file}")
        except Exception as e:
            self.logger.error(f"读取标准唤醒配置文件失败: {e}")
        
        self.logger.info(f"建立单参数池完成，共 {len(self.single_param_pool)} 个可用参数：")
        for param in self.single_param_pool:
            self.logger.info(f"  - {param['param_config']['name']} (来源: {param['source']})")

    def classify_cases(self) -> None:
        """整理case_list并划分成不同类型的用例"""
        # 初始化
        self.expected_time_type1 = None
        self.expected_case_type1 = []
        self.error_time_type1 = None
        self.error_case_type1 = []
        self.stuck_case_type1 = []
        self.expected_time_type2 = None
        self.expected_case_type2 = []
        self.error_time_type2 = None
        self.error_case_type2 = []
        self.stuck_case_type2 = []

        if self.config.MODE == "MIX":
            for case in self.original_cases:
                for i in case['expected_results']['expected']:
                    if type(i["in_put"]) == type({}):
                        self.expected_case_type1.extend([i])
                    else:
                        self.expected_case_type2.extend([i])

            for case in self.original_cases:
                for i in case['error_results']['error']:
                    if type(i["in_put"]) == type({}):
                        self.error_case_type1.append({
                            "in_put": i["in_put"],
                            "error": i["error"]
                        })
                        self.stuck_case_type1.append({
                            "in_put": i["in_put"],
                            "stuck": i["stuck"]
                        })
                    else:
                        self.error_case_type2.append({
                            "in_put": i["in_put"],
                            "error": i["error"]
                        })
                        self.stuck_case_type2.append({
                            "in_put": i["in_put"],
                            "stuck": i["stuck"]
                        })
        else:
            # expected_time和expected_case
            for case in self.original_cases:
                expected_results = case.get("expected_results", {})
                expected_type = expected_results.get("type")
                expected_list = expected_results.get("expected", [])

                if expected_type == 1:
                    if self.expected_time_type1 is None:
                        self.expected_time_type1 = expected_results.get("time")
                    self.expected_case_type1.extend(expected_list)

                elif expected_type == 2:
                    if self.expected_time_type2 is None:
                        self.expected_time_type2 = expected_results.get("time")
                    self.expected_case_type2.extend(expected_list)

            # error_time_和error_cases和stuck_cases
            for case in self.original_cases:
                error_results = case.get("error_results", {})
                error_type = error_results.get("type")
                error_group_list = error_results.get("error", [])

                if error_type == 1:
                    if self.error_time_type1 is None:
                        self.error_time_type1 = error_results.get("time")
                    for group in error_group_list:
                        in_put = group.get("in_put", {})
                        error_list = group.get("error", [])
                        stuck_list = group.get("stuck", [])

                        self.error_case_type1.append({
                            "in_put": in_put,
                            "error": error_list
                        })
                        self.stuck_case_type1.append({
                            "in_put": in_put,
                            "stuck": stuck_list
                        })

                elif error_type == 2:
                    if self.error_time_type2 is None:
                        self.error_time_type2 = error_results.get("time")
                    for group in error_group_list:
                        in_put = group.get("in_put", {})
                        error_list = group.get("error", [])
                        stuck_list = group.get("stuck", [])

                        self.error_case_type2.append({
                            "in_put": in_put,
                            "error": error_list
                        })
                        self.stuck_case_type2.append({
                            "in_put": in_put,
                            "stuck": stuck_list
                        })


    def generate_value(self, in_put: Dict[str, Any]) -> Any:
        """
        根据给定的 in_put 生成对应的随机值
        :param in_put: 包含生成信息的字典
        :return: 生成的随机值
        """
        in_type = in_put.get("in_type")
        in_range = in_put.get("in_range")
        min_value = float(in_put.get("min", 0))
        max_value = in_put.get("max")
        if max_value != '':
            max_value = float(max_value)
        step_len = float(in_put.get("step_len", 1))
        
        # 如果 in_type 为 2，直接返回最小值1
        if in_type == 2:
            return min_value

        # 如果 in_type 为 1，范围内生成随机值
        # 用到了 in_range ，但其实 in_range = 2就是 in_type = 2
        if in_type == 1:
            if in_range == 1:  # 不包含边界值
                range_size = (max_value - min_value) / step_len
                random_index = random.randint(1, int(range_size) - 1)
                value = min_value + random_index * step_len
            elif in_range == 2:  # 固定值单值
                return min_value
            
            # 根据 step_len 对生成的随机值进行四舍五入
            return value

        # 3. 如果不符合条件，则返回 None 或抛出异常（视需求）
        self.logger.error(f"无法处理in_type为{in_type}的输入配置：{in_put}")
        return None

    def get_param_values(self, param: Dict) -> List:
        """获取参数的可能值列表"""
        if param["in_type"] == 2:  # 固定值
            return [float(param["min"])]

        #if param["enum_type"] == 1:  # 枚举值
            #return param["enum_list"]

        # 确保数值参数是数字类型
        try:
            min_val = float(param["min"])
            max_val = float(param["max"])
            step = float(param.get("step_len", 1))
        except (ValueError, TypeError) as e:
            self.logger.error(f"参数值转换失败: {str(e)}")
            return []

        # 生成候选值序列
        try:
            values = list(np.arange(min_val, max_val + step, step))
            values = np.round(values, 1).tolist()
        except Exception as e:
            self.logger.error(f"生成参数值序列失败: {str(e)}")
            return []

        # 处理不包含边界的情况
        if param.get("in_range", 0) == 1:  # 默认包含边界
            values = [
                v for v in values
                if not (np.isclose(v, min_val) or np.isclose(v, max_val))
            ]

        return values

    def find_original_param_config(self, name: str, type: int) -> Optional[Dict]:
        """根据参数ID查找原始配置"""
        # 搜索type1用例
        if type == 1:
            for case in self.expected_case_type1:
                in_put = case["in_put"]
                if isinstance(in_put, dict) and in_put.get("name") == name:
                    return in_put
                elif isinstance(in_put, list):
                    for param in in_put:
                        if param.get("name") == name:
                            return param

        # 搜索type2用例
        elif type == 2:
            for case in self.expected_case_type2:
                in_put = case["in_put"]
                if isinstance(in_put, dict) and in_put.get("name") == name:
                    return in_put
                elif isinstance(in_put, list):
                    for param in in_put:
                        if param.get("name") == name:
                            return param


        self.logger.error(f"未找到原始参数配置: ID={name}")
        return None

    def regenerate_case_metadata(self, new_case: Dict, original_config: Dict) -> None:
        """重新生成用例的元数据"""
        # 查找原始用例和类型
        case_type = self.current_case["type"]
        original_case = self.find_original_case(original_config, case_type)
        if not original_case:
            return

        # 根据类型获取对应的错误信息
        error_group = self.error_case_type1 if case_type == 1 else self.error_case_type2
        stuck_group = self.stuck_case_type1 if case_type == 1 else self.stuck_case_type2
        expected_time = self.expected_time_type1 if case_type == 1 else self.expected_time_type2

        try:
            # 查找原始用例在对应类型用例列表中的索引
            case_list = self.expected_case_type1 if case_type == 1 else self.expected_case_type2
            idx = case_list.index(original_case)

            # 更新预期结果和错误信息
            new_case.update({
                "expected_results": original_case["out_put"],
                "error": [
                    {"error_type": 1, "out_data": error_group[idx]["error"]},
                    {"error_type": 2, "out_data": stuck_group[idx]["stuck"]}
                ],
                "est_time": expected_time
            })
        except (ValueError, IndexError) as e:
            self.logger.error(f"匹配原始用例错误信息失败: {str(e)}")

    def find_original_case(self, param_config: Dict, type: int) -> Tuple[Optional[Dict], Optional[int]]:
        """根据参数配置查找原始用例和类型"""
        # 在type1用例中查找
        if type == 1:
            for case in self.expected_case_type1:
                in_put = case["in_put"]
                if isinstance(in_put, dict) and in_put.get("uuid") == param_config.get("uuid"):
                    return case, 1
                elif isinstance(in_put, list):
                    for param in in_put:
                        if param.get("uuid") == param_config.get("uuid"):
                            return case

        # 在type2用例中查找
        elif type == 2:
            for case in self.expected_case_type2:
                in_put = case["in_put"]
                if isinstance(in_put, dict) and in_put.get("uuid") == param_config.get("uuid"):
                    return case, 2
                elif isinstance(in_put, list):
                    for param in in_put:
                        if param.get("uuid") == param_config.get("uuid"):
                            return case

        return None, None



    