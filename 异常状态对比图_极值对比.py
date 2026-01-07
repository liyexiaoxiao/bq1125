import json
import matplotlib.pyplot as plt
import sqlite3
import os
import numpy as np

# 设置中文字体，确保中文正常显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

SQLALCHEMY_DATABASE_URI = os.path.join('app', 'replay.db')


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

    def detect_extrema(self, values):
        """
        检测极值点位置（极大值和极小值）
        返回: (极大值索引列表, 极小值索引列表)
        """
        if len(values) < 3:
            return [], []
        
        maxima = []
        minima = []
        
        for i in range(1, len(values) - 1):
            # 极大值：比前后都大
            if values[i] > values[i-1] and values[i] > values[i+1]:
                maxima.append(i)
            # 极小值：比前后都小
            elif values[i] < values[i-1] and values[i] < values[i+1]:
                minima.append(i)
        
        return maxima, minima

    def compare_trends(self, values1, values2, tolerance=1):
        """
        比较两个序列的变化趋势
        tolerance: 允许的位置偏差（单位：索引位置）
        返回: 趋势不一致的位置列表
        """
        maxima1, minima1 = self.detect_extrema(values1)
        maxima2, minima2 = self.detect_extrema(values2)
        
        anomaly_indices = []
        
        # 检查极大值位置是否匹配
        for idx1 in maxima1:
            # 允许一定的位置偏差
            if not any(abs(idx1 - idx2) <= tolerance for idx2 in maxima2):
                anomaly_indices.append(idx1)
        
        # 检查极小值位置是否匹配
        for idx1 in minima1:
            if not any(abs(idx1 - idx2) <= tolerance for idx2 in minima2):
                anomaly_indices.append(idx1)
        
        # 也检查对方有但己方没有的极值点
        for idx2 in maxima2:
            if not any(abs(idx2 - idx1) <= tolerance for idx1 in maxima1):
                if idx2 not in anomaly_indices:
                    anomaly_indices.append(idx2)
        
        for idx2 in minima2:
            if not any(abs(idx2 - idx1) <= tolerance for idx1 in minima1):
                if idx2 not in anomaly_indices:
                    anomaly_indices.append(idx2)
        
        return sorted(set(anomaly_indices))

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

            # 提取值序列用于趋势分析
            values1 = [p[1] for p in common_data1]
            values2 = [p[1] for p in common_data2]
            
            # 检测两条曲线的极值点
            maxima1, minima1 = self.detect_extrema(values1)
            maxima2, minima2 = self.detect_extrema(values2)
            
            # 找出趋势不一致的位置（极值点位置不匹配）
            trend_anomaly_indices = self.compare_trends(values1, values2, tolerance=1)
            
            # 转换为实际的数据序号
            batch_anomalies = []
            for local_idx in trend_anomaly_indices:
                data_index = common_data1[local_idx][0]
                val1 = values1[local_idx]
                val2 = values2[local_idx]
                
                # 判断是什么类型的异常
                anomaly_type = []
                if local_idx in maxima1:
                    anomaly_type.append(f"{name1}极大值")
                if local_idx in minima1:
                    anomaly_type.append(f"{name1}极小值")
                if local_idx in maxima2:
                    anomaly_type.append(f"{name2}极大值")
                if local_idx in minima2:
                    anomaly_type.append(f"{name2}极小值")
                
                anomaly_info = {
                    "data_index": data_index,
                    f"{name1}_value": val1,
                    f"{name2}_value": val2,
                    "anomaly_type": ", ".join(anomaly_type) if anomaly_type else "趋势不一致"
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

            # 标记极大值点（信号1）
            for local_idx in maxima1:
                data_index = common_data1[local_idx][0]
                value = values1[local_idx]
                plt.plot(data_index, value, 'r^', markersize=10, 
                        label=f'{name1}极大值' if local_idx == maxima1[0] else "")
            
            # 标记极小值点（信号1）
            for local_idx in minima1:
                data_index = common_data1[local_idx][0]
                value = values1[local_idx]
                plt.plot(data_index, value, 'rv', markersize=10, 
                        label=f'{name1}极小值' if local_idx == minima1[0] else "")
            
            # 标记极大值点（信号2）
            for local_idx in maxima2:
                data_index = common_data2[local_idx][0]
                value = values2[local_idx]
                plt.plot(data_index, value, 'b^', markersize=10, 
                        label=f'{name2}极大值' if local_idx == maxima2[0] else "")
            
            # 标记极小值点（信号2）
            for local_idx in minima2:
                data_index = common_data2[local_idx][0]
                value = values2[local_idx]
                plt.plot(data_index, value, 'bv', markersize=10, 
                        label=f'{name2}极小值' if local_idx == minima2[0] else "")

            # 标记趋势不一致的位置（用垂直虚线）
            for anomaly in batch_anomalies:
                data_index = anomaly["data_index"]
                plt.axvline(x=data_index, color='red', linestyle=':', alpha=0.5,
                            label='趋势异常' if data_index == batch_anomalies[0]["data_index"] else "")
                plt.text(data_index, plt.ylim()[1], f'第{data_index}个',
                         rotation=90, verticalalignment='top',
                         color='red', fontweight='bold', fontsize=8)

            # 在标题中显示该批次的异常数量
            if batch_anomalies:
                anomaly_indices = [str(a["data_index"]) for a in batch_anomalies]
                title_anomaly_info = f'(趋势异常数据: 第{",".join(anomaly_indices)}个, 共{len(batch_anomalies)}处)'
            else:
                title_anomaly_info = '(趋势一致，无异常)'

            plt.title(
                f'{name1} 与 {name2} 趋势对比曲线 (批次 {batch_num}: 第{start_idx + 1}-{end_idx}个数据) {title_anomaly_info}')
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
            print(f"   信号1 极大值点: {len(maxima1)}个, 极小值点: {len(minima1)}个")
            print(f"   信号2 极大值点: {len(maxima2)}个, 极小值点: {len(minima2)}个")
            if batch_anomalies:
                print(f"   该批次发现 {len(batch_anomalies)} 处趋势异常，对应数据序号: 第{', '.join(anomaly_indices)}个")
            else:
                print(f"   该批次趋势一致，未发现异常")

        # 输出总体异常统计
        print(f"\n📊 所有批次处理完成，共 {len(batches)} 批数据，保存目录: '{save_dir}'")
        print(f"🔍 总计发现 {len(all_anomalies)} 处趋势异常数据")

        # 将所有异常信息保存到JSON文件（只包含指定字段）
        if all_anomalies:
            anomaly_file = os.path.join(save_dir, "趋势异常数据汇总.json")
            with open(anomaly_file, 'w', encoding='utf-8') as f:
                json.dump(all_anomalies, f, ensure_ascii=False, indent=2)
            print(f"📄 趋势异常详细信息已保存至: {anomaly_file}")


# 执行程序
db = YourDatabaseClass()
db.plot_batch_combined_curves(
    save_dir="../report/8/replay_comparison_plots/PDCU输出快充唤醒信号状态_vs_整车状态",
    name1="PDCU输出快充唤醒信号状态",
    name2="整车状态",
    batch_size=100  # 每100个数据为一个批次
)
db.plot_batch_combined_curves(
    save_dir="../report/8/replay_comparison_plots/充放电枪连接指示灯_vs_整车状态",
    name1="充放电枪连接指示灯",
    name2="整车状态",
    batch_size=100  # 每100个数据为一个批次
)
db.plot_batch_combined_curves(
    save_dir="../report/8/replay_comparison_plots/动力防盗允许READY标志位_vs_整车状态",
    name1="动力防盗允许READY标志位",
    name2="整车状态",
    batch_size=100  # 每100个数据为一个批次
)
db.plot_batch_combined_curves(
    save_dir="../report/8/replay_comparison_plots/快充唤醒信号_vs_整车状态",
    name1="快充唤醒信号",
    name2="整车状态",
    batch_size=100  # 每100个数据为一个批次
)
db.plot_batch_combined_curves(
    save_dir="../report/8/replay_comparison_plots/整车State状态_vs_整车状态",
    name1="整车State状态",
    name2="整车状态",
    batch_size=100  # 每100个数据为一个批次
)
db.plot_batch_combined_curves(
    save_dir="../report/8/replay_comparison_plots/整车禁止READY标志位_vs_整车状态",
    name1="整车禁止READY标志位",
    name2="整车状态",
    batch_size=100  # 每100个数据为一个批次
)
db.plot_batch_combined_curves(
    save_dir="../report/8/replay_comparison_plots/整车模式_vs_整车状态",
    name1="整车模式",
    name2="整车状态",
    batch_size=100  # 每100个数据为一个批次
)
db.plot_batch_combined_curves(
    save_dir="../report/8/replay_comparison_plots/直流充电枪连接状态_vs_整车状态",
    name1="直流充电枪连接状态",
    name2="整车状态",
    batch_size=100  # 每100个数据为一个批次
)