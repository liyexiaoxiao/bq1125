import os
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')


# 获取当前目录
current_directory = os.getcwd()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    # 测试数据目录
    DATA_DIR = os.path.join(current_directory, "testdata") + os.sep
    # 用例生成个数
    RUN_TIMES = 50
    # 模式：混合、全s、全w

    # 测试平台URL
    TEST_PALTFORM_URL = "http://127.0.0.1:8080"
    # 数据库对接地址
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
    #                           'mysql+mysqlconnector://root:admin123@localhost:3306/test?charset=utf8'  # 在开发环境中连接本地mysql数据库

    _db_path = os.environ.get('DATABASE_FILE_PATH') or os.path.join(basedir, 'app', 'db.db')
    DATABASE = _db_path
    
    if os.environ.get('SQLALCHEMY_DATABASE_URI'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    else:
        if _db_path.startswith("/") or _db_path[1] == ':':
             SQLALCHEMY_DATABASE_URI = 'sqlite:///' + _db_path
        else:
             SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath(_db_path)

    REPLAY_SOURCE_DATABASE_URI = os.environ.get('REPLAY_SOURCE_DATABASE_URI') or _db_path
    REPLAY_DATABASE_URI = os.environ.get('REPLAY_DATABASE_URI') or os.path.join(basedir, 'app', 'replay.db')

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
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
    TESTING = True
    SECRET_KEY = 'test_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    pass
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
    #                           'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
