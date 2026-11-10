# -*- coding: utf-8 -*-
"""网站5（数据库开发）数据库连接配置。

沿用通用模板的连接方式，把连接参数集中放在这里。
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
