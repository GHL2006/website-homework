# -*- coding: utf-8 -*-
"""初始化 MySQL 数据库：创建 organic 表，并把 data/organic.csv 导入数据库。

用法（在 webapp 目录下）：
    python init_db.py

脚本会删除并重建 organic 表，然后导入 CSV 中的 271 条有机物记录。
运行前请确认 MySQL80 服务已启动，并且已经按 sql/setup.sql 创建好
数据库 web 和账号 web。
"""
from __future__ import print_function

import csv
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(os.path.dirname(BASE_DIR), ".deps")

# 优先使用 pip 安装的 PyMySQL，没有安装时使用项目自带的 .deps
try:
    import pymysql  # noqa: E402
except ImportError:
    if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
        sys.path.insert(0, VENDOR_DIR)
    import pymysql  # noqa: E402

from config import DB_CONFIG, ORGANIC_TABLE  # noqa: E402

CSV_FILE = os.path.join(BASE_DIR, "data", "organic.csv")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `{table}` (
    `id` INT NOT NULL,
    `name` VARCHAR(100) NOT NULL COMMENT '名称',
    `formula` VARCHAR(100) DEFAULT NULL COMMENT '分子式',
    `cas` VARCHAR(50) DEFAULT NULL COMMENT 'CAS 号',
    `molecular_weight` VARCHAR(50) DEFAULT NULL COMMENT '分子量',
    `melting_point` VARCHAR(50) DEFAULT NULL COMMENT '熔点',
    `boilling_point` VARCHAR(50) DEFAULT NULL COMMENT '沸点',
    `density` VARCHAR(50) DEFAULT NULL COMMENT '密度',
    `refractive` VARCHAR(50) DEFAULT NULL COMMENT '折射率',
    `purity` VARCHAR(100) DEFAULT NULL COMMENT '纯度',
    `flash_point` VARCHAR(50) DEFAULT NULL COMMENT '闪点',
    `explosion_limit` VARCHAR(50) DEFAULT NULL COMMENT '爆炸极限',
    PRIMARY KEY (`id`),
    KEY `idx_name` (`name`),
    KEY `idx_cas` (`cas`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='有机物数据表'
""".format(table=ORGANIC_TABLE)

INSERT_SQL = """
INSERT INTO `{table}` (
    `id`, `name`, `formula`, `cas`, `molecular_weight`, `melting_point`,
    `boilling_point`, `density`, `refractive`, `purity`, `flash_point`,
    `explosion_limit`
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""".format(table=ORGANIC_TABLE)

COLUMNS = [
    "id", "name", "formula", "cas", "molecular_weight", "melting_point",
    "boilling_point", "density", "refractive", "purity", "flash_point",
    "explosion_limit",
]


def load_csv_rows():
    """读取 CSV，把空字符串转换成 NULL，返回可以直接写入数据库的元组列表。"""
    if not os.path.exists(CSV_FILE):
        raise SystemExit("找不到数据文件：%s" % CSV_FILE)

    result = []
    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for line_number, raw in enumerate(reader, start=2):
            values = []
            for column in COLUMNS:
                value = (raw.get(column) or "").strip()
                if column == "id":
                    values.append(int(value))
                else:
                    values.append(value if value else None)
            if not values[1]:
                continue
            result.append(tuple(values))
    return result


def main():
    rows = load_csv_rows()
    print("CSV 数据读取完成，共 %d 条记录。" % len(rows))

    print("正在连接 MySQL：%s@%s:%s/%s ..." % (
        DB_CONFIG["user"], DB_CONFIG["host"], DB_CONFIG["port"],
        DB_CONFIG["database"],
    ))
    conn = pymysql.connect(autocommit=False, **DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS `%s`" % ORGANIC_TABLE)
            cursor.execute(CREATE_TABLE_SQL)
            cursor.executemany(INSERT_SQL, rows)
        conn.commit()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM `%s`" % ORGANIC_TABLE)
            total = cursor.fetchone()[0]
            print("导入完成：%s 表共有 %d 条记录。" % (ORGANIC_TABLE, total))

            cursor.execute(
                "SELECT id, name, formula, cas, molecular_weight, boilling_point "
                "FROM `%s` WHERE name LIKE %%s ORDER BY id"
                % ORGANIC_TABLE,
                ("%甲醛%",),
            )
            print("验证查询：名称包含“甲醛”的记录 ->")
            for item in cursor.fetchall():
                print("   ", item)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
