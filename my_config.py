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
    RUN_TIMES = 50
    # 模式：混合、全s、全w

    # 测试平台URL
    TEST_PALTFORM_URL = "http://127.0.0.1:8080"
    # 数据库对接地址
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
    #                           'mysql+mysqlconnector://root:admin123@localhost:3306/test?charset=utf8'  # 在开发环境中连接本地mysql数据库

    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    # SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    # FLASKY_MAIL_SENDER = '119161229@qq.com'
    # FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    # SQLALCHEMY_TRACK_MODIFICATIONS = True

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
# class DevelopmentConfig(Config):
#     DEBUG = True
#     MAIL_SERVER = 'smtp.qq.com'
#     MAIL_PORT = 587
#     MAIL_USE_TLS = True
#     MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
#     MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
#     SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
#                               'mysql+mysqlconnector://root:admin123@localhost:3306/test?charset=utf8'  # 在开发环境中连接本地mysql数据库


class TestingConfig(Config):
    TESTING = False
    # SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or \
    #                           'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


# class ProductionConfig(Config):
#     SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
#                               'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    # 'production': ProductionConfig,
    'default': DevelopmentConfig
}
