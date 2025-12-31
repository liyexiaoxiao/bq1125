import json
import matplotlib.pyplot as plt
import sqlite3
import os

# 设置中文字体，确保中文正常显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

SQLALCHEMY_DATABASE_URI = os.path.join('app', 'db.db')


class YourDatabaseClass:
    def get_db_connection(self):
        conn = sqlite3.connect(SQLALCHEMY_DATABASE_URI)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_test_runs(self):
        conn = self.get_db_connection()
        runs = conn.execute('SELECT * FROM test_runs').fetchall()
        conn.close()
        return [dict(run) for run in runs]

    # 按数据序号标记异常，JSON只保留指定字段
    def plot_batch_combined_curves(self, save_dir="./comparison_plots",
                                   name1="快充唤醒信号",
                                   name2="动力防盗允许READY标志位",
                                   batch_size=100):

        os.makedirs(save_dir, exist_ok=True)

        # 获取所有测试数据
        runs = self.get_all_test_runs()
        total_runs = len(runs)
        print(f"总测试数据量: {total_runs} 个")

        # 计算批次数量
        batches = [(i, min(i + batch_size, total_runs))
                   for i in range(0, total_runs, batch_size)]

        # 存储所有异常信息（只保留需要的字段）
        all_anomalies = []

        # 按批次处理数据
        for batch_num, (start_idx, end_idx) in enumerate(batches, 1):
            batch_runs = runs[start_idx:end_idx]
            print(f"处理第 {batch_num} 批数据 (数据范围: 第{start_idx + 1}个 - 第{end_idx}个)")

            # 收集当前批次中两个信号的数据
            data = {
                name1: [],
                name2: []
            }

            for idx, run in enumerate(batch_runs):
                # 数据序号 = 起始索引 + 当前索引 + 1（从1开始计数）
                data_index = start_idx + idx + 1  # 这就是"第几个数据"
                run_id = run.get('id', data_index)  # 使用数据序号作为备用run_id
                actual_output_str = run.get('actual_output', '')

                if not actual_output_str:
                    continue

                try:
                    actual_output = json.loads(actual_output_str)
                    data_list = actual_output.get("data", [])
                    if not isinstance(data_list, list):
                        continue

                    # 提取两个目标信号的值
                    current_values = {name1: None, name2: None}
                    for item in data_list:
                        if item.get("name") == name1:
                            current_values[name1] = item.get("value")
                        elif item.get("name") == name2:
                            current_values[name2] = item.get("value")

                    # 只记录两个信号都有值的数据点
                    if current_values[name1] is not None and current_values[name2] is not None:
                        data[name1].append((data_index, current_values[name1]))  # 用数据序号作为x轴
                        data[name2].append((data_index, current_values[name2]))

                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    print(f"解析出错 (第{data_index}个数据): {e}")
                    continue

            # 如果当前批次没有有效数据则跳过
            if not data[name1] or not data[name2]:
                print(f"⚠️ 第 {batch_num} 批无有效数据，跳过绘图")
                continue

            # 确保数据按数据序号排序
            for name in data:
                data[name].sort(key=lambda x: x[0])

            # 找到两个信号在当前批次中的共同数据序号
            indices1 = {p[0] for p in data[name1]}
            indices2 = {p[0] for p in data[name2]}
            common_indices = indices1 & indices2

            # 提取共同数据点
            common_data1 = [p for p in data[name1] if p[0] in common_indices]
            common_data2 = [p for p in data[name2] if p[0] in common_indices]
            common_data1.sort(key=lambda x: x[0])
            common_data2.sort(key=lambda x: x[0])

            # 找出值不同的位置（只记录需要的字段）
            batch_anomalies = []
            for (data_index, val1), (_, val2) in zip(common_data1, common_data2):
                if val1 != val2:
                    # 只保留三个必要字段
                    anomaly_info = {
                        "data_index": data_index,
                        f"{name1}_value": val1,
                        f"{name2}_value": val2
                    }
                    batch_anomalies.append(anomaly_info)
                    all_anomalies.append(anomaly_info)

            # 绘制当前批次的对比曲线
            plt.figure(figsize=(12, 6))

            # 绘制两个信号的曲线（x轴为数据序号）
            plt.plot([p[0] for p in common_data1], [p[1] for p in common_data1],
                     marker='o', linestyle='-', label=name1, alpha=0.7)
            plt.plot([p[0] for p in common_data2], [p[1] for p in common_data2],
                     marker='s', linestyle='--', label=name2, alpha=0.7)

            # 标记值不同的位置并显示数据序号（第几个数据）
            for anomaly in batch_anomalies:
                data_index = anomaly["data_index"]
                # 绘制垂直线标记异常位置
                plt.axvline(x=data_index, color='red', linestyle=':', alpha=0.7,
                            label='异常位置' if data_index == batch_anomalies[0]["data_index"] else "")
                # 显示是第几个数据
                plt.text(data_index, plt.ylim()[1], f'第{data_index}个',
                         rotation=90, verticalalignment='top',
                         color='red', fontweight='bold')

            # 在标题中显示该批次的异常数量
            if batch_anomalies:
                anomaly_indices = [str(a["data_index"]) for a in batch_anomalies]
                title_anomaly_info = f'(异常数据: 第{",".join(anomaly_indices)}个, 共{len(batch_anomalies)}处)'
            else:
                title_anomaly_info = '(无异常数据)'

            plt.title(
                f'{name1} 与 {name2} 对比曲线 (批次 {batch_num}: 第{start_idx + 1}-{end_idx}个数据) {title_anomaly_info}')
            plt.xlabel('数据序号（第几个数据）')  # x轴明确标记为数据序号
            plt.ylabel('Value')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()

            # 保存图像
            safe_name1 = "".join(c if c.isalnum() or c in " _-." else "_" for c in name1)
            safe_name2 = "".join(c if c.isalnum() or c in " _-." else "_" for c in name2)
            filename = f"{safe_name1}_vs_{safe_name2}_批次{batch_num}_第{start_idx + 1}-{end_idx}个数据.png"
            filepath = os.path.join(save_dir, filename)
            plt.savefig(filepath, dpi=150)
            plt.close()

            # 输出批次异常信息
            print(f"✅ 已保存第 {batch_num} 批对比图像: {filepath}")
            if batch_anomalies:
                print(f"   该批次发现 {len(batch_anomalies)} 处异常，对应数据序号: 第{', '.join(anomaly_indices)}个")
            else:
                print(f"   该批次未发现异常")

        # 输出总体异常统计
        print(f"\n📊 所有批次处理完成，共 {len(batches)} 批数据，保存目录: '{save_dir}'")
        print(f"🔍 总计发现 {len(all_anomalies)} 处异常数据")

        # 将所有异常信息保存到JSON文件（只包含指定字段）
        if all_anomalies:
            anomaly_file = os.path.join(save_dir, "异常数据汇总.json")
            with open(anomaly_file, 'w', encoding='utf-8') as f:
                json.dump(all_anomalies, f, ensure_ascii=False, indent=2)
            print(f"📄 异常详细信息已保存至: {anomaly_file}")


# 执行程序
db = YourDatabaseClass()
db.plot_batch_combined_curves(
    save_dir="./comparison_plots",
    batch_size=100  # 每100个数据为一个批次
)