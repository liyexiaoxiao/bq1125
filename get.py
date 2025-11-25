import json
import matplotlib.pyplot as plt
from collections import defaultdict
import sqlite3
import os
SQLALCHEMY_DATABASE_URI = os.path.join('app', 'db.db')

# 设置中文字体，确保中文正常显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams['axes.unicode_minus'] = False

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

    def plot_actual_output_data_curves(self, save_dir="./plots"):
        """
        从 actual_output 字段中提取 data 列表，
        为每个 name 绘制 value 随 run_id 变化的曲线图并保存。
        """
        import os
        os.makedirs(save_dir, exist_ok=True)

        # 获取所有测试运行数据
        runs = self.get_all_test_runs()

        # 使用 defaultdict(list) 来按 name 分组收集 (run_id, value) 数据
        name_data = defaultdict(list)

        # 遍历每一行数据（每个 run）
        for idx, run in enumerate(runs):
            # 使用数据库中的 id 字段作为 run_id，若没有则用 idx
            run_id = run.get('id', idx)  # 假设表中有 id 字段，否则用序号

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

        # 为每个 name 绘制曲线图
        for name, points in name_data.items():
            if len(points) == 0:
                continue

            # 按 run_id 排序（确保横坐标有序）
            points.sort(key=lambda x: x[0])
            x_vals = [p[0] for p in points]
            y_vals = [p[1] for p in points]

            plt.figure(figsize=(10, 6))
            plt.plot(x_vals, y_vals, marker='o', linestyle='-', label=name)
            plt.title(f'"{name}" 值随测试轮次变化曲线')
            plt.xlabel('Run ID')
            plt.ylabel('Value')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()

            # 清理文件名中的非法字符
            safe_name = "".join(c if c.isalnum() or c in " _-." else "_" for c in name)
            filename = f"{safe_name}_曲线图.png"
            filepath = os.path.join(save_dir, filename)

            plt.savefig(filepath, dpi=150)
            plt.close()  # 关闭图像，避免内存泄漏

            print(f"✅ 已保存图像: {filepath}")

        print(f"📈 总共生成 {len(name_data)} 张曲线图，保存在 '{save_dir}' 目录下。")
# 假设你的类实例叫 db

db = YourDatabaseClass()
db.plot_actual_output_data_curves(save_dir="./output_plots")