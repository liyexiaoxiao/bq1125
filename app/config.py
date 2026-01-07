import os
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')


# 获取当前目录
current_directory = os.getcwd()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    # 测试数据目录
    DATA_DIR = os.path.join(current_directory, "testdata")
    # 用例生成个数
    RUN_TIMES = 10
    # 模式：混合、全s、全w、重放 MIX/SLEEP/WAKE/REPLAY
    MODE = "MIX"
    REPLAY_MODE = "REPLAY"
    # 文件夹名称
    DIR_NAME = "test001"
    # 测试平台URL
    # TEST_PALTFORM_URL = "http://154.8.193.119:8020"
    TEST_PALTFORM_URL = "http://154.8.193.119:8020"
    
    # reset_api = f'{TEST_PALTFORM_URL}/api/v1/reset'
    # map_api = f'{TEST_PALTFORM_URL}/api/v1/mapping'
    # read_api = f'{TEST_PALTFORM_URL}/api/v1/read'
    # send_api = f'{TEST_PALTFORM_URL}/api/v1/send'
    
    @property
    def reset_api(self):
        return f'{self.TEST_PALTFORM_URL}/api/v1/reset'

    @property
    def map_api(self):
        return f'{self.TEST_PALTFORM_URL}/api/v1/mapping'

    @property
    def read_api(self):
        return f'{self.TEST_PALTFORM_URL}/api/v1/read'

    @property
    def send_api(self):
        return f'{self.TEST_PALTFORM_URL}/api/v1/send'
    # 数据库对接地址
    # 数据库对接地址
    # SQLALCHEMY_DATABASE_URI = "sqlite:///app/db.db"
    SQLALCHEMY_DATABASE_URI = "sqlite:///app/db.db"
    DATABASE = os.path.join(basedir, 'db.db')
    REPLAY_SOURCE_DATABASE_URI = os.path.join('app', 'db.db')
    REPLAY_DATABASE_URI = os.path.join('app', 'replay.db')
    REPLAY_START_RUN_ID = None
    REPLAY_END_RUN_ID = 21
    READ_INTERVAL = 100
    SIGNAL_TOLERANCE = 0.1
    # 变异策略模块参数
    SINGLE_VARIATION_TIME = 10
    MULTIPLE_VARIATION_TIME = 10
    REPEAT_VARIATION_TIME = 20

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    pass
    # SQLALCHEMY_DATABASE_URI = "sqlite:///app/db.db"


config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
