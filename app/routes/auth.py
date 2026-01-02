from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from app.utils.security import hash_password, generate_salt
from app.utils.operationlog import log_operation
from datetime import datetime
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
@log_operation('用户登录')
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'code': 400, 'msg': '请输入用户名和密码'})

    user = User.query.filter_by(LOGINNAME=username).first()

    if user:
        if user.SALT:
            try:
                salt = bytes.fromhex(user.SALT)
                hashed_pw = hash_password(password, salt).hex()
                if hashed_pw == user.PWD:
                    login_user(user)
                    return jsonify({'code': 200, 'msg': '登录成功'})
            except Exception as e:
                # Handle potential encoding/decoding errors silently to avoid exposing system details
                pass
    return jsonify({'code': 401, 'msg': '用户名或密码错误'})

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
@log_operation('用户登出')
def logout():
    logout_user()
    return jsonify({'code': 200, 'msg': '登出成功'})

@auth_bp.route('/api/user/add', methods=['POST'])
@login_required
@log_operation('添加用户')
def add_user():
    # Only admin can add users
    if current_user.LOGINNAME != 'admin':
        return jsonify({'code': 403, 'msg': '无权操作'})

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')

    if not username or not password:
        return jsonify({'code': 400, 'msg': '缺少必要参数'})

    if User.query.filter_by(LOGINNAME=username).first():
        return jsonify({'code': 400, 'msg': '用户已存在'})

    salt = generate_salt()
    hashed_pw = hash_password(password, salt).hex()

    new_user = User(
        ID=str(uuid.uuid4()),
        LOGINNAME=username,
        PWD=hashed_pw,
        SALT=salt.hex(),
        NAME=name,
        CREATEDATETIME=datetime.now(),
        UPDATEDATETIME=datetime.now(),
        STATUS='1' # Active
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '用户添加成功'})

@auth_bp.route('/api/check_auth', methods=['GET'])
def check_auth():
    if current_user.is_authenticated:
        return jsonify({'code': 200, 'is_authenticated': True, 'username': current_user.LOGINNAME})
    else:
        return jsonify({'code': 200, 'is_authenticated': False})
