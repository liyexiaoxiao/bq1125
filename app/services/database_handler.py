import json
import uuid
from sqlalchemy import create_engine, text, Integer
from sqlalchemy.orm import sessionmaker
from app.models.models import *
# from datetime import datetime
import time
from datetime import datetime
import sqlite3
import time
# from config import DATABASE



class TestResultHandler:
    def __init__(self, logger, db_url, app=None):
        self.logger = logger
        # self.engine = create_engine(db_url)
        # Session = sessionmaker(bind=self.engine)
        # self.session = Session()
        self.app = app
        # 处理SQLAlchemy URI，提取文件路径
        if db_url.startswith('sqlite:///'):
            self.database = db_url[10:]  # 移除 'sqlite:///' 前缀
        else:
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
                self.logger.error(f"数据库插入失败: {e}")
                return None
            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            self.logger.error(f"存储测试结果时发生异常: {e}")
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
        获取截至当前 run_id 的最近20条成功插入记录的耗时与 run_id（不分类型）
        :param run_id: 当前测试运行ID（用于限定上界）
        :return: tuple (duration_list, run_id_list, results) - 执行时间列表、run_id列表、完整记录列表；
                 出错或未找到返回 ([], [], [])
        """
        # if not run_id:
        #     self.logger.error("run_id不能为空")
        #     return None

        conn = None
        try:
            self.logger.info(f"正在查询截至 run_id={run_id} 的最近20条测试记录（不分类型）...")
            conn = self.get_db_connection()
            # 设置事务隔离级别，允许脏读，解决写后立即读的数据可见性问题
            conn.execute("PRAGMA read_uncommitted = true;")
            conn.row_factory = sqlite3.Row  # 使结果可像字典一样访问
            # 查询截至当前 run_id 的所有记录
            query_sql = """
                        SELECT run_id, \
                               round_id, \
                               actual_input, \
                               expected_output, \
                               expected_error_output, \
                               expected_stuck_output, \
                               actual_output, \
                               expected_duration, \
                               actual_duration, \
                               status, \
                               strategy, \
                               type
                        FROM test_runs
                        WHERE run_id <= ?
                        """
            cursor = conn.execute(query_sql, (run_id,))
            all_rows = cursor.fetchall()
            # print(f"[DEBUG] 数据库查询返回了 {len(all_rows)} 行数据")

            if not all_rows:
                self.logger.info(f"未找到任何测试记录")
                return [], [], []

            # 在 Python 中排序并获取最近的20条
            all_rows.sort(key=lambda r: r['run_id'], reverse=True)
            recent_rows = all_rows[:20]
            
            self.logger.info(f"查询到 {len(all_rows)} 条记录，选取最近的 {len(recent_rows)} 条进行分析。")

            # 提取字段
            duration_list = [int(row['actual_duration'] or 0) for row in recent_rows]
            run_id_list = [row['run_id'] for row in recent_rows]
            results = [dict(row) for row in recent_rows]  # 转为字典列表，便于后续使用

            self.logger.info(f"成功获取{len(duration_list)}条最近记录")
            # print(f"分析采样 run_ids: {run_id_list}")

            return duration_list, run_id_list, results

        except Exception as e:
            print(f"[DEBUG] 在 get_recent_durations 中发生异常: {e}")
            self.logger.error(f"查询测试记录失败: {str(e)}")
            # return None
            return [], [], []

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
            # print(f"[DEBUG] 开始分析时间，传入的 run_id: {run_id}")
            # 获取最近20条测试记录的耗时与run_id
            durations, related_run_ids, result_list = self.get_recent_durations(run_id)

            if len(related_run_ids) < 20:
                print("分析结果：数据不足，跳过")
                return 0
            # 将最近记录按时间升序排列（从最早到最新），保持索引一致
            durations_asc = list(reversed(durations))
            run_ids_asc = list(reversed(related_run_ids))
            # 计算相邻耗时差值
            diffs = []
            for i in range(len(durations_asc) - 1):
                diffs.append(durations_asc[i + 1] - durations_asc[i])
            # 连续增长的最小阈值（过滤抖动）
            min_increase = 100
            growth_block_start = None
            # 检查是否存在四次连续增长的片段（对应五个点）
            for start in range(len(diffs) - 3):
                if diffs[start] > min_increase and diffs[start + 1] > min_increase and diffs[start + 2] > min_increase and diffs[start + 3] > min_increase:
                    growth_block_start = start
                    break
            has_growth = growth_block_start is not None
            # 检查是否存在单次耗时超过其他组2秒以上的异常孤点
            outlier_index = None
            for i in range(len(durations_asc)):
                current = durations_asc[i]
                others = durations_asc[:i] + durations_asc[i + 1:]
                if not others:
                    continue
                if current - max(others) > 2000:
                    outlier_index = i
                    break

            # 若命中任一异常类型则记录错误日志，并记录输入
            if has_growth or outlier_index is not None:
                log_id = str(uuid.uuid4())
                error_type = 1 if has_growth else 2
                conn = None
                try:
                    # 写入错误日志到 test_error_log
                    conn = self.get_db_connection()
                    cursor = conn.cursor()
                    created_at = datetime.fromtimestamp(time.time()).isoformat()
                    cursor.execute("""
                          INSERT INTO test_error_log (log_id, error_type, created_at)
                          VALUES (?, ?, ?) 
                          """, (log_id, error_type, created_at))
                    conn.commit()
                except Exception as e:
                    if conn:
                        conn.rollback()
                    self.logger.error(str(e))
                finally:
                    if conn:
                        conn.close()

                # 确保 pro_input 表存在
                self.ensure_pro_input_table()
                result_map = {row['run_id']: row for row in result_list}
                if has_growth:
                    # 取该增长片段覆盖的4个点，并更新策略为非0（此处设为2）
                    indices = [growth_block_start, growth_block_start + 1, growth_block_start + 2, growth_block_start + 3]
                    target_run_ids = [run_ids_asc[idx] for idx in indices if idx < len(run_ids_asc)]
                    # self.update_strategy_by_run_ids(target_run_ids, 2)  这句是修改原数据记录的srategy
                    # 在 pro_input 记录这些 run 的输入（reason_type=1）
                    for rid in target_run_ids:
                        row = result_map.get(rid)
                        if not row:
                            continue
                        self.record_pro_input(rid, row.get('round_id'), row.get('type'), row.get('strategy'), row.get('actual_input'), 1, row.get('actual_duration'))
                    self.logger.warn("出现四次耗时增长")
                    print("分析结果：连续四次耗时增长")
                if outlier_index is not None:
                    # 记录孤点的输入（reason_type=2）
                    rid = run_ids_asc[outlier_index]
                    row = result_map.get(rid)
                    if row:
                        self.record_pro_input(rid, row.get('round_id'), row.get('type'), row.get('strategy'), row.get('actual_input'), 2, row.get('actual_duration'))
                    self.logger.warn("出现单次运行耗时超过其他组2秒")
                    if has_growth:
                        print("分析结果：同时存在连续增长与孤点超2秒")
                    else:
                        print("分析结果：耗时孤点超2秒")
                # 有孤点返回策略3，仅有增长返回0，其余返回0
                return 0 if has_growth and outlier_index is None else 3 if outlier_index is not None else 0

            # 未发现异常情况
            self.logger.info("20次运行中未出现异常情况")
            print("分析结果：未发现异常情况")
            return 0

        except Exception as e:
            self.logger.error(f"分析执行时间失败: {str(e)}")
            print(f"分析结果：分析执行时间失败: {str(e)}")
            return 0

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
            self.logger.debug("正在查询最新记录的round_id...")

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
                self.logger.debug("数据库中没有 test_runs 记录")
                return None

            round_id = row['round_id']
            self.logger.debug(f"成功获取最新记录的round_id: {round_id}")
            return round_id

        except Exception as e:
            self.logger.error(f"查询最新round_id失败: {str(e)}")
            return None

        finally:
            if conn:
                conn.close()

    def get_type_count_by_run_id(self, run_id):
        conn = None
        try:
            conn = self.get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT type FROM test_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            target_type = row['type']
            cursor = conn.execute("SELECT COUNT(1) AS cnt FROM test_runs WHERE type = ?", (target_type,))
            cnt_row = cursor.fetchone()
            return int(cnt_row['cnt']) if cnt_row else 0
        except Exception as e:
            self.logger.error(str(e))
            return None
        finally:
            if conn:
                conn.close()

    def ensure_pro_input_table(self):
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pro_input'")
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pro_input (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id INTEGER NOT NULL,
                        round_id INTEGER,
                        type INTEGER,
                        strategy INTEGER,
                        actual_input TEXT NOT NULL,
                        actual_duration INTEGER,
                        reason_type INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(run_id) REFERENCES test_runs(run_id)
                    )
                    """
                )
                conn.commit()
            else:
                cursor.execute("PRAGMA table_info('pro_input')")
                cols = cursor.fetchall()
                col_names = [c[1] if isinstance(c, tuple) else c['name'] for c in cols]
                if 'actual_duration' not in col_names:
                    cursor.execute("ALTER TABLE pro_input ADD COLUMN actual_duration INTEGER")
                    conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(str(e))
        finally:
            if conn:
                conn.close()

    def record_pro_input(self, run_id, round_id, type_value, strategy_value, actual_input_text, reason_type, actual_duration_value):
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            created_at = datetime.fromtimestamp(time.time()).isoformat()
            cursor.execute(
                """
                INSERT INTO pro_input (run_id, round_id, type, strategy, actual_input, actual_duration, reason_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, round_id, type_value, strategy_value, actual_input_text, int(actual_duration_value or 0), reason_type, created_at)
            )
            conn.commit()
            print(f"[DEBUG] pro_input 写入: run_id={run_id}, actual_duration={int(actual_duration_value or 0)}, reason_type={reason_type}")
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(str(e))
        finally:
            if conn:
                conn.close()

    def update_strategy_by_run_ids(self, run_ids, new_strategy):
        if not run_ids:
            return
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(run_ids))
            sql = f"UPDATE test_runs SET strategy = ? WHERE run_id IN ({placeholders})"
            cursor.execute(sql, (new_strategy, *run_ids))
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(str(e), exc_info=True)
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
            self.logger.error(f"查询 actual_output 失败: {str(e)}")
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
            self.logger.error(f"查询新状态记录失败: {str(e)}")
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
