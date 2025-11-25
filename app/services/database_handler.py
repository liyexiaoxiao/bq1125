import json
import uuid
from sqlalchemy import create_engine, text, Integer
from sqlalchemy.orm import sessionmaker
from app.models.models import *
# from datetime import datetime
import time
from datetime import datetime
import sqlite3
# from config import DATABASE



class TestResultHandler:
    def __init__(self, logger, db_url, app=None):
        self.logger = logger
        # self.engine = create_engine(db_url)
        # Session = sessionmaker(bind=self.engine)
        # self.session = Session()
        self.app = app
        self.database = db_url

    def store_test_result(self, actual_duration, test_data_file=None, test_data=None, result_data=None, strategy=0,
                          round_id=None):
        """
        将测试数据存储到数据库中
        :param actual_duration: 实际执行耗时（毫秒）
        :param test_data_file: JSON测试数据文件路径（可选）
        :param test_data: 直接传入的测试数据字典（可选）
        :param result_data: 测试执行结果数据（可选）
        :param strategy: 策略标识（0: 正常, 1/2: 新状态, -1: 平台错误, -2: 错误, -3: 卡住）
        :param round_id: 所属轮次ID（可选）
        :return: run_id (int) 插入记录的主键ID，失败返回 None
        """
        # 读取 test_data
        try:
            if test_data_file:
                self.logger.info(f"正在读取测试数据文件: {test_data_file}")
                with open(test_data_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                self.logger.info("测试数据文件读取成功")
            elif test_data is None:
                raise ValueError("必须提供 test_data_file 或 test_data 其中之一")

            # 根据 strategy 确定 status
            if strategy == 0:
                status = 1
            elif strategy in (1, 2):
                status = 4
            elif strategy == -1:
                status = -1
            elif strategy == -2:
                status = 2
            elif strategy == -3:
                status = 3
            else:
                status = 1  # 默认正常状态

            # 提取并序列化字段
            in_data = test_data.get('in_data')
            expected_results = test_data.get('expected_results')

            # 处理 error 数组：第一个为 error，第二个为 stuck
            expected_error_output = None
            expected_stuck_output = None
            errors = test_data.get('error')
            if errors and isinstance(errors, list):
                if len(errors) > 0:
                    expected_error_output = errors[0].get('out_data') if errors[0] else None
                if len(errors) > 1:
                    expected_stuck_output = errors[1].get('out_data') if errors[1] else None

            # expected_duration = int(test_data.get('est_time', 0))
            expected_duration = 20

            # 准备插入字段
            insert_values = {
                'actual_input': json.dumps(in_data, ensure_ascii=False, separators=(',', ':')),
                'expected_output': json.dumps(expected_results, ensure_ascii=False, separators=(',', ':')),
                'round_id': round_id,
                'expected_error_output': json.dumps(expected_error_output, ensure_ascii=False,
                                                    separators=(',', ':')) if expected_error_output else None,
                'expected_stuck_output': json.dumps(expected_stuck_output, ensure_ascii=False,
                                                    separators=(',', ':')) if expected_stuck_output else None,
                'actual_output': json.dumps(result_data, ensure_ascii=False,
                                            separators=(',', ':')) if result_data else None,
                'expected_duration': expected_duration,
                'actual_duration': actual_duration,
                'status': status,
                'type': test_data.get('type', 1),
                'strategy': strategy
            }

            # 构建插入语句
            sql = '''
                  INSERT INTO test_runs (actual_input, \
                                         expected_output, \
                                         round_id, \
                                         expected_error_output, \
                                         expected_stuck_output, \
                                         actual_output, \
                                         expected_duration, \
                                         actual_duration, \
                                         status, \
                                         type, \
                                         strategy) \
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                  '''

            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                self.logger.info("正在执行数据库插入操作...")
                cursor.execute(sql, (
                    insert_values['actual_input'],
                    insert_values['expected_output'],
                    insert_values['round_id'],
                    insert_values['expected_error_output'],
                    insert_values['expected_stuck_output'],
                    insert_values['actual_output'],
                    insert_values['expected_duration'],
                    insert_values['actual_duration'],
                    insert_values['status'],
                    insert_values['type'],
                    insert_values['strategy']
                ))
                conn.commit()
                new_id = cursor.lastrowid
                self.logger.info(f"数据插入成功! run_id = {new_id}")
                return new_id
            except Exception as e:
                conn.rollback()
                self.logger.error(f"数据库插入失败: {e}", exc_info=True)
                return None
            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            self.logger.error(f"存储测试结果时发生异常: {e}", exc_info=True)
            return None
    # def store_test_result(self, actual_duration, test_data_file=None, test_data=None, result_data=None,strategy=0,round_id = None):
    #     ""
    #     """
    #     将测试数据存储到数据库中
    #     :param test_data_file: JSON测试数据文件路径（可选）
    #     :param result_data: 测试执行结果数据（可选）
    #     :param test_data: 直接传入的测试数据字典（可选）
    #     :return: run_id
    #     """
    #     try:
    #         if test_data_file:
    #             # 读取JSON文件
    #             self.logger.info(f"正在读取测试数据文件: {test_data_file}")
    #             with open(test_data_file, 'r', encoding='utf-8') as f:
    #                 test_data = json.load(f)
    #             self.logger.info("测试数据文件读取成功")
    #         elif test_data is None:
    #             return ValueError("必须提供test_data_file或test_data其中之一")
    #
    #         # 获取策略为0表示状态正常
    #         if strategy == 0:
    #             status = 1
    #         # 获取策略为1/2表示状态正常
    #         elif strategy == 1 or strategy == 2:
    #             status = 4
    #         # 获取策略为-1表示系统平台有误，非测试的问题
    #         elif strategy == -1:
    #             status = -1
    #         # 获取策略为-2表示状态错误
    #         elif strategy == -2:
    #             status = 2
    #         # 获取策略为-3表示状态卡住
    #         elif strategy == -3:
    #             status = 3
    #         # 准备插入数据
    #         insert_data = TestRuns(
    #             actual_input=json.dumps(test_data.get('in_data')),
    #             expected_output=json.dumps(test_data.get('expected_results')),
    #             round_id=round_id,
    #             expected_error_output=json.dumps(test_data.get('error')[0].get('out_data') if test_data.get('error') else None),
    #             expected_stuck_output=json.dumps(test_data.get('error')[1].get('out_data') if test_data.get('error') and len(test_data.get('error')) > 1 else None),
    #             actual_output=json.dumps(result_data),  # 实际输出需要从测试执行结果中获取
    #             expected_duration=int(test_data.get('est_time', 0)),  # 转换为毫秒
    #             actual_duration=actual_duration,
    #             status=status,   # status是状态1--正常 2--错误 3--卡住 4--新状态
    #             type=test_data.get('type', 1),
    #             strategy=strategy
    #         )
    #
    #         self.logger.info("正在执行数据库插入操作...")
    #         self.session.add(insert_data)
    #         self.session.commit()
    #         self.logger.info("数据插入成功!")
    #
    #         new_id = insert_data.run_id
    #         return new_id
    #
    #     except Exception as e:
    #
    #         self.logger.error(f"数据插入失败: {str(e)}")
    #         return Exception(f"存储测试结果失败: {str(e)}")

    def get_db_connection(self):
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_test_runs(self):
        """只返回数据，不涉及 Flask 的 jsonify"""
        conn = self.get_db_connection()
        runs = conn.execute('SELECT * FROM test_runs').fetchall()
        conn.close()
        return [dict(run) for run in runs]

    def get_test_run_by_id(self, run_id):
        conn = self.get_db_connection()
        run = conn.execute('SELECT * FROM test_runs WHERE run_id = ?', (run_id,)).fetchone()
        conn.close()
        return dict(run) if run else None

    def get_recent_durations(self, run_id):
        """
        获取与指定run_id相同type的最近10条记录的actual_duration和run_id
        :param run_id: 测试运行ID
        :return: tuple (duration_list, run_id_list, results) - 执行时间列表、run_id列表、完整记录列表；
                 如果出错或未找到，返回 None
        """
        if not run_id:
            self.logger.error("run_id不能为空")
            return None

        conn = None
        try:
            self.logger.info(f"正在查询run_id为{run_id}的相关测试记录...")
            conn = self.get_db_connection()
            conn.row_factory = sqlite3.Row  # 使结果可像字典一样访问

            # 第一步：根据 run_id 获取 type
            cursor = conn.execute("SELECT type FROM test_runs WHERE run_id = ?", (run_id,))
            base_row = cursor.fetchone()
            if not base_row:
                self.logger.warning(f"未找到 run_id={run_id} 的记录")
                return None
            target_type = base_row['type']

            # 第二步：查询相同 type 的最近10条记录（run_id 降序）
            query_sql = """
                        SELECT run_id, \
                               actual_duration, \
                               expected_duration, \
                               status, \
                               strategy,
                               actual_input, \
                               expected_output, \
                               expected_error_output, \
                               expected_stuck_output,
                               actual_output, \
                               type, \
                               round_id, \
                               created_at
                        FROM test_runs
                        WHERE type = ?
                        ORDER BY run_id DESC LIMIT 10 \
                        """
            cursor = conn.execute(query_sql, (target_type,))
            rows = cursor.fetchall()

            if not rows:
                self.logger.info(f"未找到 type={target_type} 的任何记录")
                return [], [], []

            # 提取字段
            duration_list = [int(row['actual_duration']) for row in rows if row['actual_duration'] is not None]
            run_id_list = [row['run_id'] for row in rows]
            results = [dict(row) for row in rows]  # 转为字典列表，便于后续使用

            self.logger.info(f"成功获取{len(duration_list)}条 type={target_type} 的最近记录")

            return duration_list, run_id_list, results

        except Exception as e:
            self.logger.error(f"查询测试记录失败: {str(e)}", exc_info=True)
            return None

        finally:
            if conn:
                conn.close()
    # def get_recent_durations(self, run_id):
    #     """
    #     获取与指定run_id相同type的最近10条记录的actual_duration和run_id
    #     :param run_id: 测试运行ID
    #     :return: tuple (duration_list, run_id_list) - 执行时间列表和对应的run_id列表
    #     """
    #     try:
    #         if not run_id:
    #             return ValueError("run_id不能为空")
    #
    #         self.logger.info(f"正在查询run_id为{run_id}的相关测试记录...")
    #         with self.app.app_context():
    #             result = TestRuns.query.filter_by(run_id=run_id).first()
    #             if result is not None:
    #                 type = result.type
    #             else:
    #                 return None
    #             results = TestRuns.query.order_by(TestRuns.run_id.desc()).limit(10).all()
    #             # 分别提取actual_duration和run_id值并转换为列表
    #             duration_list = [int(record.actual_duration) for record in results if
    #                              record.actual_duration is not None]
    #             run_id_list = [record.run_id for record in results]
    #             # duration_list = [int(row[0]) for row in results]
    #             # run_id_list = [row[1] for row in results]
    #             self.logger.info(f"成功获取{len(duration_list)}条相关记录的执行时间")
    #
    #         return duration_list, run_id_list, results
    #
    #     except Exception as e:
    #         self.logger.error(f"查询测试记录失败: {str(e)}")
    #         return Exception(f"查询测试记录失败: {str(e)}")

    def analyze_durations(self, run_id):
        """
        分析时间序列并根据条件创建日志
        :param run_id: 测试运行ID
        :return: strategy值 (0 或 3)
        """
        try:
            # 获取最近的10条记录的执行时间和对应的run_id
            durations, related_run_ids, result_list = self.get_recent_durations(run_id)
            if len(durations) < 10:  # 至少需要2条记录才能进行分析
                return 0

            # 检查是否存在线性增长
            is_linear = True
            diff = durations[1] - durations[0]  # 第一组差值
            tolerance = 100  # 允许100ms的误差范围
            
            for i in range(1, len(durations)-1):
                current_diff = durations[i+1] - durations[i]
                if abs(current_diff - diff) > tolerance:
                    is_linear = False
                    break

            # 检查是否有一组数超过其他组2秒以上
            has_outlier = False
            for i in range(len(durations)):
                current = durations[i]
                others = durations[:i] + durations[i+1:]
                if all(abs(current - other) > 2 for other in others):
                    has_outlier = True
                    # 將相应参数设置为3
                    result_list[i].status = 3
                    # self.session.commit()
                    break

            if is_linear or has_outlier:
                # 生成日志ID
                log_id = str(uuid.uuid4())
                error_type = 1 if is_linear else 2
                # 准备插入数据
                try:
                    self.logger.info("正在执行错误日志数据库插入操作...")

                    # 获取当前时间作为创建时间
                    created_at = datetime.fromtimestamp(time.time()).isoformat()  # 格式: YYYY-MM-DDTHH:MM:SS

                    # 或者可以直接用: created_at = datetime.now().isoformat()

                    conn = self.get_db_connection()
                    cursor = conn.cursor()

                    sql = """
                          INSERT INTO test_error_log (log_id, error_type, created_at)
                          VALUES (?, ?, ?) \
                          """
                    cursor.execute(sql, (log_id, error_type, created_at))
                    conn.commit()

                    self.logger.info(f"错误日志插入成功! log_id={log_id}, error_type={error_type}")
                    return True

                except Exception as e:
                    if conn:
                        conn.rollback()
                    self.logger.error(f"错误日志插入失败: {str(e)}", exc_info=True)
                    return False

                finally:
                    if conn:
                        conn.close()

                for related_run_id in related_run_ids:
                    # 假设已经存在或新创建了这些对象
                    run = TestRuns(run_id=related_run_id)  # 或者从数据库中查询现有的记录
                    log = TestErrorLog(log_id=log_id)  # 或者从数据库中查询现有的记录

                    # 将日志添加到测试运行的日志列表中
                    log.error_logs.append(run)

                    # 提交更改
                    self.session.add(run)
                    self.session.commit()

                # return 3 if has_outlier else 0
                if has_outlier:
                    self.logger.warn("出现一组数据中有数据超过2秒")
                    return 3
                if is_linear:
                    self.logger.warn("出现运行时间线性增长")
                    return 0

            self.logger.info("10次运行中未出现异常情况")
            return 0

        except Exception as e:
            self.logger.error(f"分析执行时间失败: {str(e)}")
            return Exception(f"分析执行时间失败: {str(e)}")

    # def get_latest_round_id(self): # ****新增：获取数据库中最新一条记录的round_id****
    #     """
    #     获取数据库中最新一条记录的round_id
    #     :return: round_id 如果没有记录或发生异常则返回None
    #     """
    #     try:
    #         self.logger.info("正在查询最新记录的round_id...")
    #         with self.app.app_context():
    #             # 查询最新的一条记录
    #             latest_record = TestRuns.query.order_by(TestRuns.run_id.desc()).first()
    #             self.session.fin
    #             if latest_record is None:
    #                 self.logger.info("数据库中没有记录")
    #                 return None
    #
    #             round_id = latest_record.round_id
    #             self.logger.info(f"成功获取最新记录的round_id: {round_id}")
    #             return round_id
    #
    #     except Exception as e:
    #         self.logger.error(f"查询最新round_id失败: {str(e)}")
    #         return None
    def get_latest_round_id(self):
        """
        获取数据库中最新一条记录的round_id（按run_id降序取第一条）
        :return: int | None - 最新记录的round_id，如果没有记录或发生异常则返回None
        """
        conn = None
        try:
            self.logger.info("正在查询最新记录的round_id...")

            conn = self.get_db_connection()
            conn.row_factory = sqlite3.Row  # 支持按列名访问

            # 查询 run_id 最大的那条记录的 round_id
            cursor = conn.execute("""
                                  SELECT round_id
                                  FROM test_runs
                                  ORDER BY run_id DESC LIMIT 1
                                  """)
            row = cursor.fetchone()

            if row is None:
                self.logger.info("数据库中没有 test_runs 记录")
                return None

            round_id = row['round_id']
            self.logger.info(f"成功获取最新记录的round_id: {round_id}")
            return round_id

        except Exception as e:
            self.logger.error(f"查询最新round_id失败: {str(e)}", exc_info=True)
            return None

        finally:
            if conn:
                conn.close()

    import json
    import sqlite3

    def get_first_actual_output_by_round_and_type(self, round_id, type):
        """
        获取指定round_id和type的第一条记录的actual_output（按run_id升序）
        :param round_id: 测试轮次ID
        :param type: 测试类型
        :return: dict | str | None - 解析后的 actual_output（若为JSON则转为dict），否则返回原始字符串；未找到则返回 None
        """
        conn = None
        try:
            self.logger.info(f"正在查询 round_id={round_id} 且 type={type} 的第一条记录的 actual_output...")

            conn = self.get_db_connection()
            conn.row_factory = sqlite3.Row  # 支持按列名访问

            cursor = conn.execute("""
                                  SELECT actual_output
                                  FROM test_runs
                                  WHERE round_id = ?
                                    AND type = ?
                                  ORDER BY run_id ASC LIMIT 1
                                  """, (round_id, type))

            row = cursor.fetchone()

            if row is None:
                self.logger.info(f"未找到 round_id={round_id} 且 type={type} 的记录")
                return None

            actual_output = row['actual_output']

            # 如果是字符串，尝试解析为 JSON
            if isinstance(actual_output, str) and actual_output.strip():
                try:
                    parsed = json.loads(actual_output)
                    self.logger.debug("成功将 actual_output 解析为 JSON")
                    return parsed
                except json.JSONDecodeError:
                    self.logger.warning("actual_output 不是有效的 JSON，返回原始字符串")
                    return actual_output

            return actual_output

        except Exception as e:
            self.logger.error(f"查询 actual_output 失败: {str(e)}", exc_info=True)
            return None

        finally:
            if conn:
                conn.close()

    def get_new_status_by_round(self, round_id):
        """
        获取指定 round_id 且 strategy 属于 [1,2,3] 的所有记录（用于新状态处理）
        :param round_id: 测试轮次ID
        :return: list of dict - 匹配记录的字典列表；未找到或出错返回空列表
        """
        conn = None
        try:
            self.logger.info(f"正在查询 round_id={round_id} 且 strategy IN [1,2,3] 的所有记录...")

            conn = self.get_db_connection()
            conn.row_factory = sqlite3.Row  # 支持按列名访问

            cursor = conn.execute("""
                                  SELECT run_id,
                                         actual_input,
                                         expected_output,
                                         round_id,
                                         expected_error_output,
                                         expected_stuck_output,
                                         actual_output,
                                         expected_duration,
                                         actual_duration,
                                         status,
                                         type,
                                         strategy
                                  FROM test_runs
                                  WHERE round_id = ?
                                    AND strategy IN (1, 2, 3)
                                  ORDER BY run_id ASC
                                  """, (round_id,))

            rows = cursor.fetchall()

            if not rows:
                self.logger.info(f"未找到 round_id={round_id} 且 strategy IN [1,2,3] 的记录")
                return []

            result_list = [dict(row) for row in rows]
            self.logger.info(f"成功获取 {len(result_list)} 条新状态记录")
            return result_list

        except Exception as e:
            self.logger.error(f"查询新状态记录失败: {str(e)}", exc_info=True)
            return []

        finally:
            if conn:
                conn.close()
    # def get_first_actual_output_by_round_and_type(self, round_id, type): # ****新增：获取指定round_id和type的第一条记录的actual_output,用于比对****
    #     """
    #     获取指定round_id和type的第一条记录的actual_output
    #     :param round_id: 测试轮次ID
    #     :param type: 测试类型
    #     :return: actual_output 如果没有记录或发生异常则返回None
    #     """
    #     try:
    #         self.logger.info(f"正在查询round_id={round_id}和type={type}的第一条记录的actual_output...")
    #
    #         # 查询满足条件的第一条记录
    #         record = TestRuns.query.filter_by(
    #             round_id=round_id,
    #             type=type
    #         ).first()
    #
    #         if record is None:
    #             self.logger.info(f"未找到round_id={round_id}和type={type}的记录")
    #             return None
    #
    #         actual_output = record.actual_output
    #         # 如果actual_output是JSON字符串，解析它
    #         if actual_output and isinstance(actual_output, str):
    #             try:
    #                 actual_output = json.loads(actual_output)
    #             except json.JSONDecodeError:
    #                 self.logger.warning("actual_output不是有效的JSON字符串，返回原始字符串")
    #
    #         self.logger.info(f"成功获取actual_output")
    #         return actual_output
    #
    #     except Exception as e:
    #         self.logger.error(f"查询actual_output失败: {str(e)}")
    #         return None
    #
    # def get_new_status_by_round(self, round_id):  # ****新增：获取指定round_id和type的第一条记录的actual_output,用于比对****
    #     """
    #     获取指定round_id和type的第一条记录的actual_output,用于比对
    #     :param round_id: 测试轮次ID
    #     :return: actual_output 如果没有记录或发生异常则返回None
    #     """
    #     try:
    #         self.logger.info(f"正在查询round_id={round_id}")
    #         with self.app.app_context():
    #             # 查询满足条件的第一条记录
    #             record = TestRuns.query.filter(TestRuns.round_id == round_id,TestRuns.strategy.in_([1, 2, 3]),).all()
    #             if record is None:
    #                 self.logger.info(f"未找到round_id={round_id}的记录")
    #                 return None
    #
    #             # actual_output = record.actual_output
    #             # # 如果actual_output是JSON字符串，解析它
    #             # if actual_output and isinstance(actual_output, str):
    #             #     try:
    #             #         actual_output = json.loads(actual_output)
    #             #     except json.JSONDecodeError:
    #             #         self.logger.warning("actual_output不是有效的JSON字符串，返回原始字符串")
    #
    #             self.logger.info(f"成功获取actual_output")
    #             return record
    #
    #     except Exception as e:
    #         self.logger.error(f"查询actual_output失败: {str(e)}")
    #         return None

    def compare_result_with_first_wake(self, round_id, result_data):
        """
        比较当前result_data与同一round_id下type=1的第一次唤醒返回的actual_output
        
        :param round_id: 测试轮次ID
        :param result_data: 当前测试结果数据
        :return: 如果有信号发生变化则返回1，否则返回0
        """
        try:
            self.logger.info(f"正在比较当前结果与round_id={round_id}的第一次唤醒结果...")
            
            # 获取同一round_id下type=1的第一条记录的actual_output
            first_wake_output = self.get_first_actual_output_by_round_and_type(round_id, 1)
            
            if first_wake_output is None:
                self.logger.info("未找到第一次唤醒记录，无法比较")
                return 0
                
            # 确保result_data是字典类型
            if isinstance(result_data, str):
                try:
                    result_data = json.loads(result_data)
                except json.JSONDecodeError:
                    self.logger.error("当前result_data不是有效的JSON字符串")
                    return 0
                    
            # 比较两个结果中的信号值
            has_changes = False
            
            # 遍历当前结果中的每个信号
            for signal in result_data:
                # 在第一次唤醒结果中查找相同名称的信号
                for first_signal in first_wake_output:
                    if signal.get('name') == first_signal.get('name'):
                        # 比较信号值
                        if signal.get('value') != first_signal.get('value'):
                            self.logger.info(f"信号 {signal.get('name')} 发生变化: {first_signal.get('value')} -> {signal.get('value')}")
                            has_changes = True
                        break
            
            if has_changes:
                self.logger.info("检测到信号变化")
                return 1
            else:
                self.logger.info("未检测到信号变化")
                return 0
                
        except Exception as e:
            self.logger.error(f"比较结果失败: {str(e)}")
            return 0