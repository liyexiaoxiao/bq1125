import json
import time

import requests


def _clean_response_text(response):
    """清理响应内容，避免日志中出现HTML代码"""
    try:
        if response.status_code in [502, 503, 504]:
            return f"Server Error {response.status_code}"
        
        text = response.text.strip()
        if text.startswith("<!DOCTYPE") or text.startswith("<html") or text.startswith("<head"):
            return f"Server returned HTML content (Status: {response.status_code})"
        return text
    except Exception:
        return "Error reading response text"


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
            self.logger.error(f"测试平台接口交互模块---发送复位消息---失败: {_clean_response_text(response)}")
            return False
        else:
            self.logger.info("测试平台接口交互模块---发送复位消息---成功")
        
        try:
            response_json = response.json()
            if response_json.get("ok") == 1:
                return True
            else:
                self.logger.error(f"测试平台接口交互模块---发送复位消息---失败: {response_json}")
                return False
        except Exception:
            self.logger.error(f"测试平台接口交互模块---发送复位消息---失败: {_clean_response_text(response)}")
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
            print(f"Response Body: {_clean_response_text(response)}")
            try:
                json_data = response.json()  # 自动处理 bytes -> str -> dict/list
                print("JSON Data:", json_data)
            except requests.exceptions.JSONDecodeError as e:
                print("响应内容不是有效的 JSON 格式:", e)
                print("原始文本内容:", _clean_response_text(response))
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
    except Exception as e:
        self.logger.error(f"测试平台接口交互模块---发送复位消息---异常: {str(e)}")
        return False


def read_api(self):
    try:
        read_url = self.config.read_api
        # 获取需要读取的信号列表（插件变量名）
        signal_names = list(self.signal_mapping.values())

        if not signal_names:
            self.logger.error("没有配置需要读取的信号")
            return {
                "status": "error",
                "message": "没有配置需要读取的信号",
                "timestamp": time.time()
            }

        # 准备请求数据（mock 平台期望: {"signals": [...]}）
        payload = {"signals": signal_names, "mode": 0}

        # 发送请求
        response = requests.post(read_url, json=payload)

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
        send_url = self.config.send_api
        # 准备请求数据（mock 平台期望: 列表 [{signal, val}]）
        payload = []
        signal_data = self.ensure_list(signal_data)
        for item in signal_data:
            signal_name = item["name"]
            signal_value = item["value"]

            # 获取映射的变量名
            mapped_signal = self.signal_mapping.get(signal_name, signal_name)
            payload.append({
                "signal": mapped_signal,
                "val": float(signal_value) if isinstance(signal_value, str) else signal_value
            })

        # 发送请求
        self.logger.info(f"发送信号: {json.dumps(payload, ensure_ascii=False)}")
        response = requests.post(send_url, json=payload)

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
