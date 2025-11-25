import sqlite3

# 连接数据库（文件会自动创建）
conn = sqlite3.connect('app/db.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''
CREATE TABLE test_runs (
    run_id INTEGER PRIMARY KEY,
    round_id INTEGER NOT NULL,
    actual_input TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    expected_error_output TEXT,
    expected_stuck_output TEXT,
    actual_output TEXT,
    expected_duration INTEGER NOT NULL,
    actual_duration INTEGER NOT NULL,
    status INTEGER NOT NULL,
    type INTEGER NOT NULL,
    strategy INTEGER NOT NULL
);
''')
cursor.execute('''
CREATE TABLE test_run_log_relation (
    log_id TEXT NOT NULL,
    run_id INTEGER NOT NULL,
    PRIMARY KEY (log_id, run_id),
    FOREIGN KEY (log_id) REFERENCES test_error_log (log_id) ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY (run_id) REFERENCES test_runs (run_id) ON DELETE CASCADE ON UPDATE RESTRICT
) WITHOUT ROWID;
''')
cursor.execute('''
CREATE TABLE test_error_log (
    log_id TEXT NOT NULL,
    run_id INTEGER NOT NULL,
    PRIMARY KEY (log_id, run_id)
) WITHOUT ROWID;
''')

# 提交并关闭
conn.commit()
conn.close()