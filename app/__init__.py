from flask import Flask, request
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
# from app.config import config
from flask_login import LoginManager
import flask_excel as excel
from flask_migrate import Migrate
from flask import json
from datetime import datetime, date
import sys
from flask_login import current_user
from flask import jsonify
from functools import wraps
import threading
from .utils.log_ctrl import Logger

from flask_simple_captcha import CAPTCHA

# from app.services.process_control import ProcessCtrl

CAPTCHA_CONFIG = {
    'SECRET_CAPTCHA_KEY': '5984d2c2-2721-4f51-85bf-dfcc7aedd03',
    'CAPTCHA_LENGTH': 4,
    'CAPTCHA_DIGITS': True,
    'EXPIRE_SECONDS': 600,
}

def setup_logger():
    log = Logger()

    return log

def permission(permission_id):
    def need_permission(func):
        @wraps(func)
        def inner(*args, **kargs):
            if not current_user.ID:
                return jsonify(401, {"msg": "认证失败，无法访问系统资源"})
            else:
                resources = []
                resourceTree = []

                resources += [res for org in current_user.organizations for res in org.resources if org.resources]
                resources += [res for role in current_user.roles for res in role.resources if role.resources]
                
                # remove repeat
                new_dict = dict()
                for obj in resources:
                    if obj.ID not in new_dict:
                        new_dict[obj.ID] = obj

                for resource in new_dict.values():
                    resourceTree.append(resource.PERMS)
                if permission_id in resourceTree:
                    return func(*args, **kargs)
                else:
                    return jsonify({'msg': '当前操作没有权限', 'code': 403})
        return inner
    return need_permission
        


# Replace this line:
# JSONEncoder = json.JSONEncoder

# With this:
try:
    # For Flask 2.0+
    from flask.json.provider import JSONEncoder
except ImportError:
    try:
        # For older Flask versions
        from flask.json import JSONEncoder
    except ImportError:
        # Fallback for very new Flask versions
        from flask.json.provider import DefaultJSONProvider as JSONEncoder

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return JSONEncoder.default(self, obj)

loginmanager = LoginManager()
loginmanager.session_protection = 'strong'
#loginmanager.login_view = 'base.login'

moment = Moment()
db = SQLAlchemy()
captcha = CAPTCHA(config=CAPTCHA_CONFIG)


def create_app(config_name):
    app = Flask(__name__)
    if config_name is None:
        config_name = "development"
    if config_name == "development":
        # sys.path.append("F:\\北汽\\codelast\\git_fuzz\\configs")
        app.config.from_object("my_config.DevelopmentConfig")
    elif config_name == "production":
        app.config.from_object("my_config.ProductionConfig")
    elif config_name == "testing":
        app.config.from_object("my_config.TestingConfig")

    #  替换默认的json编码器
    app.json_encoder = CustomJSONEncoder
    # app.config.from_object(config[config_name])
    # config[config_name].init_app(app)

    moment.init_app(app)
    db.init_app(app)
    Migrate(app, db)
    loginmanager.init_app(app)
    captcha.init_app(app)

    from .base import base as base_blueprint
    app.register_blueprint(base_blueprint)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    @app.before_request
    def check_login():
        if request.method == 'OPTIONS':
            return
        
        # Allow static resources if served by Flask
        if request.endpoint and 'static' in request.endpoint:
            return
            
        # Allow auth routes
        if request.endpoint and request.endpoint.startswith('auth.'):
            return

        # Explicitly allow login/logout if not covered by above (though they are in auth)
        if request.path in ['/api/login', '/api/logout']:
            return

        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({'code': 401, 'msg': '未登录，请先登录'}), 401

    excel.init_excel(app)

    return app

