import os
import json


class DataInit:
    def __init__(self, logger, config):
        # 初始化存储数据的列表
        # self.json_data_list = []
        # self.assert_data_list = []
        self.case_list = []
        self.in_data_range = []
        self.out_data_range = []
        self.success_data = []
        self.error_data = []
        # type==0 初始化状态  type==1单输入信号  type==2多输入信号
        # self.in_data_dict = {"type": 0, "in_data": []}
        # self.out_data_dict = {"type": 0, "in_data": []}

        self.logger = logger
        self.data_dir = config.DATA_DIR + config.DIR_NAME

    def read_file(self, filename):
        file_path = os.path.join(self.data_dir, filename)
        # 打开并读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # 将 JSON 数据解析为字典
                json_data = json.load(file)
                # 将字典添加到列表中
                return json_data, None
        except Exception as e:
            self.logger.error(f"Error reading file {filename}: {e.args[0]}")
            return None, e

    def load_json_files(self):
        """
        从指定目录中读取符合要求的 JSON 文件，并将内容加载为字典列表。

        :param
        :return:
        """
        self.logger.info("start load_json_files")
        file_num = os.listdir(self.data_dir)
        if len(file_num) == 0:
            self.logger.error("no json_files")
            return None, None, Exception

        json_data_list = []
        assert_data_list = []
        # 遍历指定目录下的所有文件
        for filename in os.listdir(self.data_dir):
            # 检查文件名是否以 'test_' 开头并以 '.json' 结尾
            if filename.startswith('test_') and filename.endswith('.json'):
                json_data, err = self.read_file(filename)
                if err is not None:
                    self.logger.error("read_file error")
                    return None, None, err
                json_data_list.append(json_data)

            # 检查文件名是否以 'assert_' 开头并以 '.json' 结尾
            if filename.startswith('assert_') and filename.endswith('.json'):
                json_data, err = self.read_file(filename)
                if err is not None:
                    self.logger.error("read_file error")
                    return None, None, err
                assert_data_list.append(json_data)
        return json_data_list, assert_data_list, None

    def data_dict(self, t):
        # 判断positive_values列表是否为空
        if len(t["value_set"]["positive_values"]) == 0:
            data = {
                "name": t["name"],  # 名称
                "enum_type": 0,        # 是否枚举标志位  0-否   1-是
                "data_type": t["data_type"],  # 数据类型
                "step_len": t["factor"],  # 变异步长
                "max_value": t["ranges"][0]["max_value"],  # 最大值
                "min_value": t["ranges"][0]["min_value"],  # 最小值
                "ID": t["uuid"]  # 参数唯一ID
            }
        else:
            data = {
                "name": t["name"],  # 名称
                "enum_type": 1,  # 是否枚举标志位  0-否   1-是
                "data_type": t["data_type"],  # 数据类型
                "step_len": t["factor"],  # 变异步长
                "max_value": t["ranges"][0]["max_value"],  # 最大值
                "min_value": t["ranges"][0]["min_value"],  # 最小值
                "ID": t["uuid"],  # 参数唯一ID
                "enum_list": t["value_set"]["positive_values"]    # 枚举参数列表
            }
        return data

    def get_case_list(self):
        return self.case_list

    def separate_data(self):
        """
        从JSON数据列表中分离出，in输入参数，out状态返回参数，确定标准预期，确定标准错误。
        标准预期、标准错误定义
            in_type 1--范围内取值 2--固定值
            in_range  1--不包含边界值  2--固定值单值
            out_type 1--阈值类型
            out_range  1--大于等于 2--等于  3--小于等于
        :param
        :return: in输入参数列表，out状态返回参数列表，确定标准预期，确定标准错误
        """
        # 加载目录下文件
        json_data_list, assert_data_list, err = self.load_json_files()

        # 运行异常，返回错误
        if err is not None:
            self.logger.error("load_json_files run error")
            return False, err

        # 数量对不上，返回错误
        if len(json_data_list) != len(assert_data_list):
            return False, "json数据和assert数据不配对"

        else:

            i = 0
            while i < len(json_data_list):

                # 用例类型变量
                case_type = json_data_list[i]["case_type"]
                # 出入参详细信息列表
                io_info_detail = json_data_list[i]["types"]

                if case_type == 1:
                    # 初始化
                    in_data_range_dict = {"type": 1, "in_data": []}
                    out_data_range_dict = {"type": 1, "out_data": []}
                    for t in io_info_detail:
                        # 出参入参值
                        direction = t["direction"]
                        # 输入信号参数范围插入
                        if direction == "in":
                            # 组织数据
                            data = self.data_dict(t)
                            # 插入数据
                            in_data_range_dict["in_data"].append(data)

                        # 状态反馈参数范围插入
                        if direction == "out":
                            # 组织数据
                            data = self.data_dict(t)
                            # 插入数据
                            out_data_range_dict["out_data"].append(data)
                    # 标准预期
                    expected_data_dict = {"type": 1, "time": 20, "expected": []}
                    for k in assert_data_list[i]["value"]:
                        expected_data_dict["expected"].append({"in_put": k["in_put"],
                                                               "out_put": k["out_put"]})
                    # 错误&卡顿预期
                    error_data_dict = {"type": 1, "time": 20, "error": []}
                    for k in assert_data_list[i]["value"]:
                        error_data_dict["error"].append({"in_put": k["in_put"],
                                                            "error": k["error"],
                                                            "stuck": k["stuck"]})
                    # 向列表中插入数据
                    self.case_list.append({"out_data_range_dict": out_data_range_dict,
                                           "in_data_range_dict": in_data_range_dict,
                                           "expected_results": expected_data_dict,
                                           "error_results": error_data_dict})

                elif case_type == 2:
                    # 初始化
                    in_data_range_dict = {"type": 2, "in_data": []}
                    out_data_range_dict = {"type": 2, "out_data": []}
                    for t in io_info_detail:
                        # 出参入参值
                        direction = t["direction"]
                        # 输入信号参数范围插入
                        if direction == "in":
                            # 组织数据
                            data = self.data_dict(t)
                            # 插入数据
                            in_data_range_dict["in_data"].append(data)

                        # 状态反馈参数范围插入
                        if direction == "out":
                            # 组织数据
                            data = self.data_dict(t)
                            # 插入数据
                            out_data_range_dict["out_data"].append(data)
                    # 标准预期
                    expected_data_dict = {"type": 2, "time": 60, "expected": []}
                    for k in assert_data_list[i]["value"]:
                        expected_data_dict["expected"].append({"in_put": k["in_put"],
                                                               "out_put": k["out_put"]})
                    # 错误&卡顿预期
                    error_data_dict = {"type": 2, "time": 60, "error": []}
                    for k in assert_data_list[i]["value"]:
                        error_data_dict["error"].append({"in_put": k["in_put"],
                                                            "error": k["error"],
                                                            "stuck": k["stuck"]})
                    # 向表中插入数据
                    self.case_list.append({"out_data_range_dict": out_data_range_dict,
                                           "in_data_range_dict": in_data_range_dict,
                                           "expected_results": expected_data_dict,
                                           "error_results": error_data_dict})
                else:
                    self.logger.error("出现未定义参数值")
                    return False, "未定义参数值"

                i += 1
            return True, None
