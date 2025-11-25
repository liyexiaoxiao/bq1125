import json
import time

import requests


# 复位API
def api_reset(self):
    try:
        # reset_url = f"{self.config.TEST_PALTFORM_URL}/api/v1/reset"
        reset_url = self.config.reset_api
        reset_data = {
            "type": 1,  # 1-恢复
            "signals": []  # 恢复模式下不需要指定信号
        }
        response = requests.post(reset_url, json=reset_data)
        if response.status_code != 200:
            self.logger.error(f"测试平台接口交互模块---发送复位消息---失败: {response.text}")
            return False
        else:
            self.logger.info("测试平台接口交互模块---发送复位消息---成功")
        response_json = response.json()
        if response_json.get("ok") == 1:
            return True
        else:
            self.logger.error(f"测试平台接口交互模块---发送复位消息---失败: {response.text}")
            return False
    except Exception as e:
        self.logger.error(f"测试平台接口交互模块---发送复位消息---异常: {str(e)}")
        return False


# 获取mapping
def api_get_map(self):
    try:
        # url = "https://krunapi.vtest.work:8020/api/v1/mapping"
        url = self.config.map_api

        # 请求头（可以根据需要添加更多字段，例如 Content-Type）
        headers = {

        }
        # 请求体（注意路径使用双反斜杠或原始字符串）
        data = {
            "mapPath": r"C:\Users\Administrator\Desktop\混沌测试\mapping\映射文件.json"
        }
        # 发送 POST 请求
        try:
            response = requests.post(url, json=data, headers=headers, verify=True)  # verify=True 表示验证 SSL 证书

            # 打印响应状态码和响应内容
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
            try:
                json_data = response.json()  # 自动处理 bytes -> str -> dict/list
                print("JSON Data:", json_data)
            except requests.exceptions.JSONDecodeError as e:
                print("响应内容不是有效的 JSON 格式:", e)
                print("原始文本内容:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
    except Exception as e:
        self.logger.error(f"测试平台接口交互模块---发送复位消息---异常: {str(e)}")
        return False


def read_api(self):
    try:
        # read_api = "https://krunapi.vtest.work:8020/api/v1/read"
        read_api = self.config.read_api
        # 获取需要读取的信号列表
        signal_names = list(self.signal_mapping.values())

        if not signal_names:
            self.logger.error("没有配置需要读取的信号")
            return {
                "status": "error",
                "message": "没有配置需要读取的信号",
                "timestamp": time.time()
            }

        # 准备请求数据
        # payload = ["整车State状态","挡位信号","蓄电池剩余电量SOC","功耗电流","总线报文发送标志位","PDCU唤醒原因","整车模式"]
        payload = ['BMS低压唤醒指令', 'CC2电压值', 'CP占空比', 'CP幅值', 'CP频率', 'DCDC过压故障', 'MCU低压唤醒指令', 'ON挡唤醒信号', 'OTA关闭交流充电指令', 'OTA私桩识别标志位', 'PDCU与BMS通讯丢失故障', 'PDCU与GW通讯丢失故障', 'PDCU输出交流充放电唤醒信号状态', 'PDCU输出快充唤醒信号状态', 'READY灯', 'S2开关控制命令', 'S2开关状态', 'VCU与BCM通讯丢失故障', 'VCU与BMS通讯丢失故障', 'VCU与DCDC通讯丢失故障', 'VCU与MCUF通讯丢失故障', 'VCU与TBOX通讯丢失故障', '与BCM通讯故障', '与DCDC通讯故障', '中控弹出充放电界面请求', '交流充放电口NTC1和NTC2温度不一致', '交流充放电口NTC1输入异常', '交流充放电口NTC2输入异常', '交流充放电口温度报警', '交流充放电座温度1', '交流充放电座温度2', '交流充放电电子锁状态反馈信号', '交流充放电线允许电流', '交流充电枪电子锁控制指令', '交流充电电流上限', '供电设备状态', '充放电控制按钮请求', '充放电枪电子锁防盗功能开启状态', '充放电枪连接指示灯', '充放电枪连接状态', '制动信号', '动力电池高压连接状态', '动力防盗允许READY标志位', '动力防盗学习状态', '右前大灯充电灯控制状态', '客户关怀需求编码_整车', '展车模式信号', '左前大灯充电灯控制状态', '快充唤醒信号', '快充握手请求标志位', '慢充唤醒信号', '慢充场景标志位', '挡位信号', '换挡器故障', '放电回路故障', '故障报警音控制指令', '整车EOL功能标志位', '整车State状态', '整车故障处理等级', '整车最高报警等级', '整车模式', '整车状态', '整车禁止READY标志位', '整车远程刷写模式需求', '档位信号', '母线电流估算值', '牵引模式使能', '牵引模式信号', '电池管理系统自检超时', '电池预加热保温需求', '电网允许最大供电电流', '电网允许的最大供电电流', '电网断电标志位', '电量低唤醒使能指令', '电量低唤醒阈值', '直流充电CC2信号异常', '直流充电口NTC1和NTC2温度不一致', '直流充电口NTC1输入异常', '直流充电口NTC2输入异常', '直流充电口温度报警', '直流充电座温度1', '直流充电座温度2', '直流充电枪连接状态', '空调暖风系统低压唤醒指令', '系统故障灯', '续驶里程', '网络唤醒信号', '蓄电池SOH', '蓄电池剩余电量SOC', '蓄电池可充电SOCEEPROM存储值', '蓄电池可充电SOC修正值', '蓄电池损坏故障', '蓄电池故障显示', '蓄电池智能充电唤醒状态', '蓄电池智能充电模式上电需求', '蓄电池智能充电禁止原因', '蓄电池智能充电结束标志位', '蓄电池电压', '蓄电池电压低', '蓄电池电压高', '车载充电机允许最大耗电功率', '车载插座供电状态', '车载插座开启关闭方式需求状态', '车载插座开启关闭需求指令', '车载插座系统使能指令', '车辆当前交流充电电流限值', '车速信号', '辅助蓄电池电量低唤醒阈值', '远程充放电需求', '远程启动状态', '远程唤醒信号', '远程控制结束标志位', '驱动功率限制指示灯', '驱动电机控制器通讯丢失', '驾驶模式信号']

        # payload = []
        # for item in self.expected_results:
        #     payload.append(item["name"])

        # 发送请求
        response = requests.post(read_api, json=payload)

        # 解析响应
        if response.status_code == 200:
            result = response.json()
            self.logger.info(f"API响应: {json.dumps(result, ensure_ascii=False)}")

            if result.get("ok") == 1:
                # 处理读取结果
                processed_results = self._process_read_results(result.get("data", {}))

                return {
                    "status": "success",
                    "timestamp": time.time(),
                    "data": processed_results
                }
            else:
                self.logger.error(f"读取信号失败: {result.get('msg')}")
                return {
                    "status": "error",
                    "message": f"读取信号失败: {result.get('msg')}",
                    "timestamp": time.time()
                }
        else:
            self.logger.error(f"API请求失败，状态码: {response.status_code}")
            return {
                "status": "error",
                "message": f"API请求失败，状态码: {response.status_code}",
                "timestamp": time.time()
            }

    except Exception as e:
        self.logger.error(f"获取测试结果时发生错误: {str(e)}")
        return {
            "status": "error",
            "message": f"获取测试结果时发生错误: {str(e)}",
            "timestamp": time.time()
        }


def send_api(self, signal_data):
    try:
        send_api = self.config.send_api
        # 准备请求数据
        payload = {}
        signal_data = self.ensure_list(signal_data)
        for item in signal_data:
            signal_name = item["name"]
            signal_value = item["value"]

            # 获取映射的变量名
            mapped_signal = self.signal_mapping.get(signal_name, signal_name)
            payload[mapped_signal] = float(signal_value) if isinstance(signal_value, str) else signal_value
            # payload.append({
            #     "signal": mapped_signal,
            #     "val": float(signal_value) if isinstance(signal_value, str) else signal_value
            # })

        # 发送请求
        self.logger.info(f"发送信号: {json.dumps(payload, ensure_ascii=False)}")
        response = requests.post(send_api, json=payload)

        # 解析响应
        if response.status_code == 200:
            result = response.json()
            self.logger.info(f"API响应: {json.dumps(result, ensure_ascii=False)}")
            return result
        else:
            self.logger.error(f"API请求失败，状态码: {response.status_code}")
            return {"ok": 0, "msg": f"API请求失败，状态码: {response.status_code}", "data": {}}
    except Exception as e:
        self.logger.error(f"发送信号时发生错误: {str(e)}")
        return {"ok": 0, "msg": f"发送信号时发生错误: {str(e)}", "data": {}}
