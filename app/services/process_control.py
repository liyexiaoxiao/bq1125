from .data_init import DataInit
from .data_variation import DataVariation
from .result_judge import ResultJudge
from .bq_api import *
from .database_handler import TestResultHandler
from .replay_runner import ReplayService



class ProcessCtrl:
    def __init__(self, logger, config, app):
        # 初始化log日志记录
        self.logger = logger
        # 所有参数集合
        self.config = config
        # 轮次--第一轮试跑、第二轮获取第一轮数据调用
        self.round_times = 1
        # 任务停止信号
        self.sing_stop = False
        self.reset = False
        self.app = app
        api_base_url = self.config.TEST_PALTFORM_URL
        self.api_base_url = api_base_url

        # self.round_id = round_id
        self.send_api = f"{self.api_base_url}/api/v1/send"
        self.read_api = f"{self.api_base_url}/api/v1/read"  # 添加读取API的URL
        self.map_api = f"{self.api_base_url}/api/v1/mapping"  # 添加读取API的URL
        self.reset_api = f"{self.api_base_url}/api/v1/reset"  # 添加读取API的URL

    # 主流程
    def run(self):
        mode = getattr(self.config, "MODE", "").strip().upper()
        replay_mode = getattr(self.config, "REPLAY_MODE", "REPLAY").strip().upper()
        if mode == replay_mode:
            self.logger.info("Process controller running in replay mode")
            self._run_replay_mode()
            return

        # TODO：获取mapping
        # api_get_map(self)

        # 初始测试结果判断模块实例前，先生成当前轮次的id：round_id
        db_handler = TestResultHandler(self.logger, db_url=self.config.DATABASE, app=self.app)
        previous_round_id = db_handler.get_latest_round_id()  # 获取最新轮次id
        # 处理没有记录或发生异常的情况
        if previous_round_id is None:
            current_round_id = 1
        else:
            # 当前轮次id为数据库中最新round_id + 1
            current_round_id = previous_round_id + 1


        while self.round_times < 3 and self.sing_stop is False:
            # 一、数据初始化模块---初始化加载数据
            data_init = DataInit(self.logger, self.config)

            #1、 第一轮,数据来源于json文档
            if self.round_times == 1:
                # 数据初始化模块---读取json数据
                _, err = data_init.separate_data()

                # 数据初始化模块---读取失败流程结果
                if err is not None:
                    self.sing_stop = True
                    self.logger.error("数据初始化模块---读取失败流程结束---失败")
                    return

                # 数据初始化模块---读取处理结果
                data = data_init.get_case_list()

                # 测试输入数据变异模块---初始化实例和初始化数据池
                data_variation = DataVariation(self.logger, self.config, case_list=data)
                # 测试输入数据变异模块---数据变异
                bak = data_variation.generate_initial_variations()

                # 测试输入数据变异模块---判断变异结果
                if bak is not True:
                    self.sing_stop = True
                    self.logger.error("测试输入数据变异模块---判断变异结果---失败")
                    return
            #2、 第二轮数据来源于数据库中的新状态数据
            else:
                # # 数据初始化模块---读取json数据
                _, err = data_init.separate_data()

                # 数据初始化模块---读取失败流程结果
                if err is not None:
                    self.sing_stop = True
                    self.logger.error("数据初始化模块---读取失败流程结束---失败")
                    return

                # 数据初始化模块---读取处理结果
                data = data_init.get_case_list()

                # 测试输入数据变异模块---初始化实例和初始化数据池
                data_variation = DataVariation(self.logger, self.config, case_list=data, app=self.app)
                # 测试输入数据变异模块---数据变异
                bak = data_variation.generate_initial_variations()

                # 测试输入数据变异模块---判断变异结果
                if bak is not True:
                    self.sing_stop = True
                    self.logger.error("测试输入数据变异模块---判断变异结果---失败")
                    return
                # data_variation = DataVariation(self.logger, self.config, case_list=data, app=self.app)
                # 测试输入数据变异模块---获取数据库新状态的结果，插入到用例池中运行
                bak = data_variation.based_new_state_fuzz(current_round_id)
                if bak:
                    pass
                else:
                    break
                pass

            # 二、测试结果判断模块---创建结果判断模块实例
            judge = ResultJudge(self.logger, config=self.config, round_id=current_round_id, app=self.app)
            while True:
                # 测试平台接口交互模块发，送复位消息，成功继续运行，失败继续下一个用例
                if not self.reset:
                    success = api_reset(self)
                    if success:
                        self.reset = True
                    else:
                        time.sleep(1)
                        continue

                # 测试输入数据变异模块---取出数据
                tast_data = data_variation.pop_first_data()
                if tast_data is None:
                    self.logger.info("测试输入数据变异模块---取出数据---结束")
                    break

                # 测试结果判断模块---处理测试数据 & 调用用例运行策略
                result = judge.process_test_data(tast_data)

                # 测试结果判断模块---处理测试数据---失败
                if 'status' in result:
                    self.logger.error("测试结果判断模块---处理测试数据---失败")
                    break

                # 测试结果判断模块---调用用例运行策略---停止
                if ('stop_signal' in result) and (result["stop_signal"] is True):
                    self.logger.error("测试结果判断模块---调用用例运行策略---停止")
                    self.sing_stop = True
                    return

                # 测试输入数据变异模块---执行对应策略
                # data_variation.trigger_variation(result)

            # 轮次加1
            self.round_times += 1

        # 测试任务结束
        self.logger.info("测试结果判断模块---调用用例运行策略---停止")




    def _run_replay_mode(self):
        self.sing_stop = False
        self.reset = False
        replay_service = ReplayService(self.logger, self.config, self.app)
        cases = replay_service.load_cases()
        if not cases:
            self.logger.warn("Replay mode did not yield any inputs to execute")
            return

        replay_config = replay_service.get_replay_config()
        judge = ResultJudge(self.logger, config=replay_config, round_id=cases[0].round_id, app=self.app)

        for case in cases:
            if not self.reset:
                if not api_reset(self):
                    self.logger.error("Replay mode reset failed; aborting replay execution")
                    return
                self.reset = True

            judge.round_id = case.round_id
            case_payload = case.payload
            case_type = case_payload.get("type")
            if case_type == 2:
                judge.test_times = 1
            else:
                judge.test_times = 0

            result = judge.process_test_data(case_payload)

            if 'status' in result:
                self.logger.error(f"Replay mode failed for source run_id={case.run_id}: {result}")
                continue

            if ('stop_signal' in result) and result["stop_signal"]:
                self.logger.warn("Replay mode received stop signal; stopping early")
                self.sing_stop = True
                break

            self.logger.info(
                f"Replay mode executed source run_id={case.run_id} with strategy {result.get('strategy')}"
            )

        self.logger.info("Replay mode execution completed")




