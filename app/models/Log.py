from app import db
from datetime import datetime
import uuid

class OperationLog(db.Model):
    __tablename__ = 'SYLOG'
    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    OPERATION_NAME = db.Column(db.String(100))
    METHOD = db.Column(db.String(10))
    PATH = db.Column(db.String(200))
    PARAMS = db.Column(db.Text)
    OPERATOR = db.Column(db.String(100))
    OPERATIONTIME = db.Column(db.Integer) # in ms
    RESULT = db.Column(db.Integer) # 1 success, 0 fail
    RESPONSE = db.Column(db.Text)
    EXCEPTION = db.Column(db.Text)
    CREATEDATETIME = db.Column(db.DateTime, default=datetime.now)
