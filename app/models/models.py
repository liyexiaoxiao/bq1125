# coding: utf-8
from flask_sqlalchemy import SQLAlchemy
from app import db

# db = SQLAlchemy()



class TestErrorLog(db.Model):

    __tablename__ = 'test_error_log'

    log_id = db.Column(db.String(36), primary_key=True, info='日志的uuid')
    error_type = db.Column(db.Integer, nullable=False, info='错误类型（1--时间线性增长，2--一组超过其他两秒以上）')
    created_at = db.Column(db.DateTime, info='日志创建时间')

    error_logs = db.relationship('TestRuns', secondary='test_run_log_relation', backref='test_error_logs')



t_test_run_log_relation = db.Table(
    'test_run_log_relation',
    db.Column('log_id', db.ForeignKey('test_error_log.log_id', ondelete='CASCADE'), primary_key=True, nullable=False, info='日志uuid'),
    db.Column('run_id', db.ForeignKey('test_runs.run_id', ondelete='CASCADE'), primary_key=True, nullable=False, index=True, info='测试记录id')
)



class TestRuns(db.Model):
    __tablename__ = 'test_runs'

    run_id = db.Column(db.Integer, primary_key=True, info='自增id')
    actual_input = db.Column(db.JSON, nullable=False, info='实际输入')
    round_id = db.Column(db.Integer, nullable=False, info='轮次id')
    expected_output = db.Column(db.JSON, nullable=False, info='预期正常输出')
    expected_error_output = db.Column(db.JSON, info='预期异常输出')
    expected_stuck_output = db.Column(db.JSON, info='预期状态卡死输出')
    actual_output = db.Column(db.JSON, info='实际输出')
    expected_duration = db.Column(db.Integer, nullable=False, info='预期执行时间(ms)')
    actual_duration = db.Column(db.Integer, nullable=False, info='实际执行时间(ms)')
    status = db.Column(db.Integer, nullable=False, info='系统状态（1--正常 2--错误 3--卡住 4--新状态）')
    type = db.Column(db.Integer, nullable=False, info='操作类型（1-唤醒操作 2-休眠操作）')
    strategy = db.Column(db.Integer, nullable=False, info='策略（-1 - 错误，-2 - 状态卡死）')
