# -*- coding: utf-8 -*-
"""数据库连接配置。

本机 MySQL 8.0 已经创建好数据库 web 和专用账号 web（只能访问 web 库），
如果换到其它电脑，请先按 sql/setup.sql 的说明创建数据库和账号，
再按 README.md 运行 init_db.py 导入数据。
"""

import os

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "web",
    "password": os.environ.get("WEB_DB_PASSWORD", ""),
    "database": "web",
    "charset": "utf8mb4",
    "connect_timeout": 5,
}

# 有机物数据表名
ORGANIC_TABLE = "organic"

# 每页最多显示的查询结果条数（与实验要求保持一致）
MAX_RESULT_ROWS = 30
