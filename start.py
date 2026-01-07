import threading
import os

from flask import request, render_template

from app import create_app
from app import setup_logger
from app.config import *
from app.services.process_control import ProcessCtrl

logger = setup_logger()

# 检查mock模式状态
mock_mode = os.getenv('MOCK_API_MODE', 'false').lower() == 'true'
if mock_mode:
    print("[MOCK模式已启用] 从本地数据库读取测试数据")
    logger.info('MOCK模式已启用: 从本地数据库读取测试数据')

    # 重置mock计数器，确保每次启动都从run_id=1开始
    import os
    mock_counter_file = "temp/mock_run_id.txt"
    if os.path.exists(mock_counter_file):
        try:
            os.remove(mock_counter_file)
            print("[MOCK模式] 计数器已重置，从run_id=1开始")
            logger.info('MOCK计数器已重置，从run_id=1开始')
        except Exception as e:
            print(f"[MOCK模式] 计数器重置失败: {e}")
            logger.warning(f'MOCK计数器重置失败: {e}')
else:
    print("[正常模式] 连接远程车架API")
    logger.info('正常模式: 连接远程车架API')

# app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app = create_app(os.getenv('FLASK_CONFIG') or "development")

logger.info('Server started')




def main():
    app.run(debug=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
