import threading

from flask import request, render_template

from app import create_app
from app import setup_logger
from app.config import *
from app.services.process_control import ProcessCtrl

logger = setup_logger()

# app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app = create_app("development")

logger.info('Server started')




def main():
    conf = Config()
    # 运行进程控制模块
    pro = ProcessCtrl(logger, conf, app)
    thread = threading.Thread(target=pro.run)
    thread.start()  # 启动线程
    thread.join()

    app.run(debug=True)


if __name__ == '__main__':
    conf = Config()
    # 运行进程控制模块
    pro = ProcessCtrl(logger, conf, app)
    
    # Run in a daemon thread so it exits when main thread receives signal
    thread = threading.Thread(target=pro.run)
    thread.daemon = True
    thread.start()

    try:
        # Keep main thread alive to handle signals
        while thread.is_alive():
            thread.join(1)
    except KeyboardInterrupt:
        logger.info("Received stop signal, exiting...")
        # Optional: pro.stop() if implemented

