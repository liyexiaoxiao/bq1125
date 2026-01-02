import hashlib
import os

def generate_salt(length=16):
    """生成随机盐"""
    return os.urandom(length)

def hash_password(password, salt):
    """使用PBKDF2算法加密密码"""
    return hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
