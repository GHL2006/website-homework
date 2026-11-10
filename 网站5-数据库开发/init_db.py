# -*- coding: utf-8 -*-
"""网站5（数据库开发）：初始化数据库并导入数据。

用法：
    python init_db.py

会创建/重建以下 4 张表并导入数据：
    lol_champion     英雄联盟棋子（86 条，来自 data/lol.csv）
    dict_word        字典词条（来自 data/dict_words.csv）
    dict_query_log   字典查询记录（初始为空，查询时写入）
    sys_user         登录用户（admin / 123456）
"""
from __future__ import print_function

import csv
import hashlib
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(os.path.dirname(BASE_DIR), ".deps")
try:
    import pymysql
except ImportError:
    sys.path.insert(0, VENDOR_DIR)
    import pymysql

from config import DB_CONFIG  # noqa: E402

CHAMPION_CSV = os.path.join(BASE_DIR, "data", "lol.csv")
DICT_CSV = os.path.join(BASE_DIR, "data", "dict_words.csv")
IMAGE_DIR = os.path.join(BASE_DIR, "static", "lol")

CREATE_TABLES = [
    """CREATE TABLE IF NOT EXISTS lol_champion (
        id INT NOT NULL COMMENT 'TFTID',
        name VARCHAR(50) NOT NULL COMMENT '棋子名称',
        title VARCHAR(100) DEFAULT NULL COMMENT '称号',
        price INT DEFAULT 0 COMMENT '卡费',
        life INT DEFAULT 0 COMMENT '生命值',
        attack INT DEFAULT 0 COMMENT '攻击力',
        armor INT DEFAULT 0 COMMENT '护甲',
        magic INT DEFAULT 0 COMMENT '魔抗',
        attack_range INT DEFAULT 0 COMMENT '攻击距离',
        attack_speed DECIMAL(4,2) DEFAULT 0 COMMENT '攻速',
        crit INT DEFAULT 0 COMMENT '暴击率',
        jobs VARCHAR(100) DEFAULT NULL COMMENT '职业',
        races VARCHAR(100) DEFAULT NULL COMMENT '种族',
        skill_name VARCHAR(100) DEFAULT NULL COMMENT '技能名称',
        skill_intro TEXT COMMENT '技能说明',
        skill_type VARCHAR(20) DEFAULT NULL COMMENT '技能类型',
        spell_block INT DEFAULT 0 COMMENT '魔抗值',
        start_magic INT DEFAULT 0 COMMENT '初始法力',
        image_file VARCHAR(50) DEFAULT NULL COMMENT '本地图片文件名',
        original_image VARCHAR(500) DEFAULT NULL COMMENT '官方原图地址',
        PRIMARY KEY (id),
        KEY idx_name (name),
        KEY idx_price (price)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='英雄联盟棋子属性表'""",
    """CREATE TABLE IF NOT EXISTS dict_word (
        id INT NOT NULL AUTO_INCREMENT,
        word VARCHAR(100) NOT NULL COMMENT '英文单词',
        phonetic VARCHAR(100) DEFAULT NULL COMMENT '音标',
        translation TEXT COMMENT '中文释义',
        PRIMARY KEY (id),
        UNIQUE KEY uk_word (word)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字典词条表'""",
    """CREATE TABLE IF NOT EXISTS dict_query_log (
        id INT NOT NULL AUTO_INCREMENT,
        username VARCHAR(50) DEFAULT NULL COMMENT '查询人',
        keyword VARCHAR(100) DEFAULT NULL COMMENT '查询关键词',
        result_count INT DEFAULT 0 COMMENT '查询结果数',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '查询时间',
        PRIMARY KEY (id),
        KEY idx_time (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字典查询记录表'""",
    """CREATE TABLE IF NOT EXISTS sys_user (
        id INT NOT NULL AUTO_INCREMENT,
        username VARCHAR(50) NOT NULL,
        password_hash CHAR(64) NOT NULL COMMENT 'sha256 密码哈希',
        display_name VARCHAR(50) DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uk_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录用户表'""",
]

DROP_TABLES = [
    "dict_query_log",
    "dict_word",
    "lol_champion",
    "sys_user",
]


def to_int(value, default=0):
    text = (value or "").strip()
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def to_float(value, default=0):
    text = (value or "").strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def load_champions():
    rows = []
    with open(CHAMPION_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            tftid = (raw.get("TFTID") or "").strip()
            if not tftid:
                continue
            image_name = "%s.jpg" % tftid
            if not os.path.exists(os.path.join(IMAGE_DIR, image_name)):
                image_name = None
            rows.append((
                int(tftid),
                (raw.get("displayName") or "").strip(),
                (raw.get("title") or "").strip() or None,
                to_int(raw.get("price")),
                to_int(raw.get("life")),
                to_int(raw.get("attack")),
                to_int(raw.get("armor")),
                to_int(raw.get("magic")),
                to_int(raw.get("attackRange")),
                to_float(raw.get("attackSpeed")),
                to_int(raw.get("crit")),
                (raw.get("jobs") or "").strip() or None,
                (raw.get("races") or "").strip() or None,
                (raw.get("skillName") or "").strip() or None,
                (raw.get("skillIntroduce") or "").strip() or None,
                (raw.get("skillType") or "").strip() or None,
                to_int(raw.get("spellBlock")),
                to_int(raw.get("startMagic")),
                image_name,
                (raw.get("originalImage") or "").strip() or None,
            ))
    return rows


def load_dict_words():
    rows = []
    with open(DICT_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            word = (raw.get("word") or "").strip()
            if not word:
                continue
            rows.append((
                word,
                (raw.get("phonetic") or "").strip() or None,
                (raw.get("translation") or "").strip() or None,
            ))
    return rows


def main():
    print("正在连接 MySQL：%s@%s:%s/%s" % (
        DB_CONFIG["user"], DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["database"]))
    conn = pymysql.connect(autocommit=False, **DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for table in DROP_TABLES:
                cur.execute("DROP TABLE IF EXISTS `%s`" % table)
            for sql in CREATE_TABLES:
                cur.execute(sql)

            champions = load_champions()
            cur.executemany(
                "INSERT INTO lol_champion (id, name, title, price, life, attack, armor, magic,"
                " attack_range, attack_speed, crit, jobs, races, skill_name, skill_intro,"
                " skill_type, spell_block, start_magic, image_file, original_image)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                champions,
            )

            words = load_dict_words()
            cur.executemany(
                "INSERT INTO dict_word (word, phonetic, translation) VALUES (%s,%s,%s)",
                words,
            )

            users = [
                ("admin", hashlib.sha256("123456".encode("utf-8")).hexdigest(), "管理员"),
                ("student", hashlib.sha256("123456".encode("utf-8")).hexdigest(), "同学"),
            ]
            cur.executemany(
                "INSERT INTO sys_user (username, password_hash, display_name) VALUES (%s,%s,%s)",
                users,
            )
        conn.commit()

        with conn.cursor() as cur:
            for table in ["lol_champion", "dict_word", "dict_query_log", "sys_user"]:
                cur.execute("SELECT COUNT(*) FROM `%s`" % table)
                print("  %-16s %d 条" % (table, cur.fetchone()[0]))
            cur.execute("SELECT id, name, price, life, jobs, races FROM lol_champion WHERE price=1 ORDER BY life DESC LIMIT 5")
            print("验证：卡费=1 的前 5 个棋子（按生命值排序）")
            for row in cur.fetchall():
                print("   ", row)
    finally:
        conn.close()
    print("数据库初始化完成。")


if __name__ == "__main__":
    main()
