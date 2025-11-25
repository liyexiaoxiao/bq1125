# coding:utf-8
from ..base import base
from ..models import User
from flask import request
from flask import jsonify
import hashlib
from flask_login import login_required, \
    current_user
from datetime import datetime
from .. import  db
import flask_excel as excel
from .. import permission
from app.utils.operationlog import log_operation
import os


@base.route('/system/user/<id>', methods=['GET'])
@login_required
@permission('system:user:query')
def syuser_getById(id):
    user = User.query.get(id)

    if user:
        json = {'code': 200, 'msg': '', 'data': user.to_json()}
        if len(user.roles.all()) > 0:
            json['roles'] = [role.to_json() for role in user.roles]
            json['roleIds'] = [role.ID for role in user.roles]

        return jsonify(json)
    else:
        return jsonify({'success': False, 'msg': 'error'})

def generate_salt(length=16):
    """生成随机盐"""
    return os.urandom(length)

def hash_password(password, salt):
    """使用PBKDF2算法加密密码"""
    return hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)

@base.route('/system/user/<id>', methods=['DELETE'])
@login_required
@permission('system:user:remove')
def syuser_delete(id):
    user = User.query.get(id)
    if user:
        db.session.delete(user)

    return jsonify({'code': 200, 'msg': '删除成功'})

@base.route('/system/user/profile/updatePwd', methods=['PUT']) 
@login_required
@log_operation('修改密码')
def syuser_update_pwd():
    user = User.query.get(current_user.ID)

    if user:
        salt = bytes.fromhex(user.SALT)
        hash = hash_password(request.args.get('oldPassword'), salt).hex()
        if hash != user.PWD:
            return jsonify({'code': 400, 'msg': '旧密码错误'})

        user.PWD = hash_password(request.args.get('newPassword'), salt).hex()
        db.session.add(user)
    return jsonify({'code': 200, 'msg': '修改成功'})

@base.route('/getInfo', methods=['GET'])
@login_required
def syuser_info():
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

    return jsonify({'msg': '登录成功~', 'code': 200, \
        'user': {'userName': current_user.LOGINNAME, 'avatar': '', 'nickName': current_user.NAME, 'userId': current_user.ID}, \
        'roles': [role.NAME for role in current_user.roles], 'permissions': resourceTree})

@base.route('/system/user/profile', methods=['GET'])
@login_required
def syuser_profile():
     return jsonify({'msg': '操作成功', 'code': 200, \
        'data': current_user.to_json(), \
        'postGroup': current_user.organizations[0].NAME if len(current_user.organizations) > 0 else '', \
        'roleGroup': [role.NAME for role in current_user.roles]})

@base.route('/system/user/profile', methods=['PUT'])
@login_required
def syuser_update_profile():
    id = request.json['userId']
    userName = request.json['userName']
    user = User.query.get(id)

    user.UPDATEDATETIME = datetime.now()
    if 'nickName' in request.json: user.NAME = request.json['nickName'] 
    if 'sex' in request.json: user.SEX = request.json['sex']
    if 'email' in request.json: user.EMAIL = request.json['email']
    if 'phonenumber' in request.json: user.PHONENUMBER = request.json['phonenumber']

    db.session.add(user)

    return jsonify({'code': 200, 'msg': '更新成功！'})

@base.route('/base/syuser/export', methods=['POST'])
@login_required
def user_export():
    rows = []
    rows.append(['登录名', '姓名', '创建时间', '修改时间', '性别'])

    users = User.query.all()
    for user in users:
        row = []
        row.append(user.LOGINNAME)
        row.append(user.NAME)
        row.append(user.CREATEDATETIME)
        row.append(user.UPDATEDATETIME)
        if user.SEX == '0':
            row.append('女')
        elif user.SEX == '1':
            row.append('男')
        rows.append(row)

    return excel.make_response_from_array(rows, "csv",
                                          file_name="user")


@base.route('/system/user/changeStatus', methods=['PUT'])
@login_required
@permission('system:user:edit')
def syuser_status_update():
    user = User.query.get(request.json['userId'])

    if 'status' in request.json: user.STATUS = request.json['status']

    db.session.add(user)

    return jsonify({'code': 200, 'msg': '操作成功'})

