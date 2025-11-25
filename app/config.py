import os
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')


# 获取当前目录
current_directory = os.getcwd()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    # 测试数据目录
    DATA_DIR = current_directory + "\\testdata\\"
    # 用例生成个数
    RUN_TIMES = 1000
    # 模式：混合、全s、全w MIX/SLEEP/WAKE
    MODE = "MIX"
    # 文件夹名称
    DIR_NAME = "test001"
    # 测试平台URL
    TEST_PALTFORM_URL = "https://krunapi.vtest.work:8020"
    # TEST_PALTFORM_URL = "http://127.0.0.1:5777"
    reset_api = f'{TEST_PALTFORM_URL}/api/v1/reset'
    map_api = f'{TEST_PALTFORM_URL}/api/v1/mapping'
    read_api = f'{TEST_PALTFORM_URL}/api/v1/read'
    send_api = f'{TEST_PALTFORM_URL}/api/v1/send'
    # 数据库对接地址
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
    #                           'mysql+mysqlconnector://root:admin123@localhost:3306/test?charset=utf8'  # 在开发环境中连接本地mysql数据库
    SQLALCHEMY_DATABASE_URI = os.path.join('app', 'db.db')
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.db')
    DATABASE = os.path.join('app', 'db.db')
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
    SQLALCHEMY_DATABASE_URI = os.path.join('app', 'db.db')
    # DEBUG = True
    # MAIL_SERVER = 'smtp.qq.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
    # #                           'mysql+mysqlconnector://root:12345678@localhost:3306/test?charset=utf8'  # 在开发环境中连接本地mysql数据库
    # # 测试数据目录
    # DATA_DIR = current_directory + "\\testdata\\"
    # # 用例生成个数
    # RUN_TIMES = 50
    # 模式：混合、全s、全w

    # 测试平台URL
    # TEST_PALTFORM_URL = "http://localhost:8080"
    # 数据库对接地址
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
    #                           'mysql+mysqlconnector://root:admin123@localhost:3306/test?charset=utf8'  # 在开发环境中连接本地mysql数据库
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    # SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    # FLASKY_MAIL_SENDER = '119161229@qq.com'
    # FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    # SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 变异策略模块参数
    # SINGLE_VARIATION_TIME = 10
    # MULTIPLE_VARIATION_TIME = 10
    # REPEAT_VARIATION_TIME = 20


# class TestingConfig(Config):
#     TESTING = False
#     SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or \
#                               'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')




config = {
    # 'development': DevelopmentConfig,
    # 'testing': TestingConfig,
    # 'production': ProductionConfig,
    'default': DevelopmentConfig
}
