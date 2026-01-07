import json
import matplotlib.pyplot as plt
from collections import defaultdict
import sqlite3
import os

# 设置中文字体，确保中文正常显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

SQLALCHEMY_DATABASE_URI = os.path.join('app', 'replay.db')


class YourDatabaseClass:  # 替换为你实际的类名
    def get_db_connection(self):
        conn = sqlite3.connect(SQLALCHEMY_DATABASE_URI)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_test_runs(self):
        """只返回数据，不涉及 Flask 的 jsonify"""
        conn = self.get_db_connection()
        runs = conn.execute('SELECT * FROM test_runs').fetchall()
        conn.close()
        return [dict(run) for run in runs]

    def plot_actual_output_data_curves(self, save_dir="./plots", batch_size=100):
        """
        从 actual_output 字段中提取 data 列表，
        为每个 name 绘制 value 随 run_id 变化的曲线图并保存。
        按每100个run_id分为一批，每批输出一组图片
        """
        import os
        os.makedirs(save_dir, exist_ok=True)

        # 获取所有测试运行数据
        runs = self.get_all_test_runs()
        total_runs = len(runs)
        batches = [(i, min(i + batch_size, total_runs)) for i in range(0, total_runs, batch_size)]

        # 为每一批数据生成图片
        for batch_num, (start_idx, end_idx) in enumerate(batches, 1):
            batch_runs = runs[start_idx:end_idx]
            batch_save_dir = os.path.join(save_dir, f"batch_{batch_num}_{start_idx}-{end_idx - 1}")
            os.makedirs(batch_save_dir, exist_ok=True)

            # 使用 defaultdict(list) 来按 name 分组收集 (run_id, value) 数据
            name_data = defaultdict(list)

            # 遍历当前批次中的每一行数据（每个 run）
            for idx, run in enumerate(batch_runs):
                # 使用数据库中的 id 字段作为 run_id，若没有则用全局索引
                global_idx = start_idx + idx
                run_id = run.get('id', global_idx)  # 假设表中有 id 字段，否则用全局序号

                actual_output_str = run.get('actual_output', '')
                if not actual_output_str:
                    continue  # 跳过空数据

                try:
                    actual_output = json.loads(actual_output_str)
                    data_list = actual_output.get("data", [])
                    if not isinstance(data_list, list):
                        continue

                    # 遍历 data 中的每个 item
                    for item in data_list:
                        name = item.get("name")
                        value = item.get("value")
                        if name is not None and value is not None:
                            name_data[name].append((run_id, value))

                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    print(f"解析 actual_output 出错 (run_id={run_id}): {e}")
                    continue

            # 为当前批次的每个 name 绘制曲线图
            for name, points in name_data.items():
                if len(points) == 0:
                    continue

                # 按 run_id 排序（确保横坐标有序）
                points.sort(key=lambda x: x[0])
                x_vals = [p[0] for p in points]
                y_vals = [p[1] for p in points]

                plt.figure(figsize=(10, 6))
                plt.plot(x_vals, y_vals, marker='o', linestyle='-', label=name)
                plt.title(f'"{name}" 值随测试轮次变化曲线 (批次 {batch_num})')
                plt.xlabel('Run ID')
                plt.ylabel('Value')
                plt.grid(True)
                plt.legend()
                plt.tight_layout()

                # 清理文件名中的非法字符
                safe_name = "".join(c if c.isalnum() or c in " _-." else "_" for c in name)
                filename = f"{safe_name}_曲线图_批次{batch_num}.png"
                filepath = os.path.join(batch_save_dir, filename)

                plt.savefig(filepath, dpi=150)
                plt.close()  # 关闭图像，避免内存泄漏

                print(f"✅ 已保存图像: {filepath}")

            print(f"📈 第 {batch_num} 批生成 {len(name_data)} 张曲线图，保存在 '{batch_save_dir}' 目录下。")

        print(f"📊 所有批次处理完成，共 {len(batches)} 批数据，总保存目录: '{save_dir}'")


db = YourDatabaseClass()
db.plot_actual_output_data_curves(save_dir="../report/3/replay_output_plots", batch_size=100)