-- 网站设计与开发实验：前后端连接 + MySQL 数据库查询
-- 在 MySQL 命令行（以 root 身份）中执行本文件，创建数据库和项目专用账号。
--
--   mysql -uroot -p < sql\setup.sql
--
-- 说明：MySQL 8.0 默认认证插件是 caching_sha2_password，PyMySQL 连接它需要
-- cryptography 依赖，所以这里给项目账号使用 mysql_native_password 认证方式，
-- 保证只安装 PyMySQL 也能正常连接。

CREATE DATABASE IF NOT EXISTS `web`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'web'@'localhost'
    IDENTIFIED WITH mysql_native_password BY 'your_password';

GRANT ALL PRIVILEGES ON `web`.* TO 'web'@'localhost';

FLUSH PRIVILEGES;

-- 之后进入 webapp 目录执行：python init_db.py
-- 会自动创建 organic 表并导入 data/organic.csv 中的 271 条数据。
