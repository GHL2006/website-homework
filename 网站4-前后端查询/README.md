# Web.py + MySQL 前后端连接实验网站

《网站设计与开发》实验：在 Bootstrap 3.3.7 五页网站的基础上，使用 **Python Web.py 0.62 + PyMySQL + MySQL 8.0** 完成前后端连接和数据库查询。前端样式与实验 3（Bootstrap 布局练习、日历、有机物查询、简历、主页）保持一致，有机物查询页面改为由 Web.py 接收表单参数、在 MySQL 数据库 `web.organic` 表中执行 SQL 查询并把结果交给模板渲染。

## 一、功能说明

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 主页 | `/index.html` | 展示本月日历（后端计算）和四个功能入口，并显示数据库记录总数 |
| 日历 | `/calendar.html` | 选择年份、月份，由 Web.py 后端用 `calendar` 模块计算，模板渲染月历 |
| 有机物查询 | `/organic.html` | 关键词 + 查询字段提交到后端，执行 `SELECT ... LIKE ...` 查询 MySQL，最多显示 30 条 |
| 简历 | `/resume.html` | Bootstrap 栅格 + 进度条的个人简历 |
| Bootstrap 样例 | `/bootstrap.html` | 胶囊导航、轮播、按钮、条纹表格组件练习 |

页面顶部使用公共的 `nav-tabs` 导航在五个页面之间切换，桌面和手机宽度下均可正常显示。

## 二、目录结构

```
网站4-前后端查询/
├── app.py                 Web.py 后端入口：页面路由、数据库查询、日历计算
├── config.py              MySQL 连接配置（数据库 web，账号 web）
├── init_db.py             创建 organic 表并导入 data/organic.csv
├── requirements.txt       依赖列表（web.py、PyMySQL）
├── run.bat                Windows 一键启动脚本
├── data/
│   └── organic.csv        有机物原始数据（271 条，UTF-8）
├── sql/
│   └── setup.sql          以 root 身份执行：创建数据库 web 和账号 web
├── static/                Bootstrap 3.3.7、jQuery 和页面样式（本地文件，不依赖外网）
└── templates/             Web.py 模板：index / calendar / organic / resume / bootstrap
```

`../.deps/` 是项目自带的 Python 依赖（web.py 0.62 和 PyMySQL 1.1.1），复制整个项目后不用再 pip 安装即可运行。如果希望自己安装依赖，也可以联网执行：

```bat
pip install web.py -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install pymysql -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

或者执行 `pip install -r requirements.txt`。`app.py` 会优先使用 pip 安装的 web.py / PyMySQL，只有在没有安装时才使用项目自带的 `.deps`，两种方式都可以运行。

## 三、数据库设计

数据库：`web`，数据表：`organic`，字符集 `utf8mb4`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INT | 序号（主键） |
| name | VARCHAR(100) | 名称 |
| formula | VARCHAR(100) | 分子式 |
| cas | VARCHAR(50) | CAS 号 |
| molecular_weight | VARCHAR(50) | 分子量 |
| melting_point | VARCHAR(50) | 熔点 |
| boilling_point | VARCHAR(50) | 沸点 |
| density | VARCHAR(50) | 密度 |
| refractive | VARCHAR(50) | 折射率 |
| purity | VARCHAR(100) | 纯度 |
| flash_point | VARCHAR(50) | 闪点 |
| explosion_limit | VARCHAR(50) | 爆炸极限 |

查询使用的 SQL（参数化，防止 SQL 注入）：

```python
# 全部字段
SELECT id, name, formula, cas, molecular_weight, boilling_point
FROM organic
WHERE name LIKE %s OR formula LIKE %s OR cas LIKE %s
ORDER BY id LIMIT 30;

# 单个字段（名称 / 分子式 / CAS 号）
SELECT ... FROM organic WHERE name LIKE %s ORDER BY id LIMIT 30;
```

## 四、运行步骤

### 1. 启动 MySQL

本机 MySQL 8.0（服务名 `MySQL80`）已安装并运行，数据库 `web`、账号 `web` 和 `organic` 表均已初始化好，直接跳到第 3 步即可。数据库密码不写进代码，运行前通过环境变量 `WEB_DB_PASSWORD` 传入（PowerShell：`$env:WEB_DB_PASSWORD="你的密码"`；CMD：`set WEB_DB_PASSWORD=你的密码`）。

如果换一台电脑，先以 root 身份执行建库脚本：

```bat
mysql -uroot -p < sql\setup.sql
```

然后在 `网站4-前后端查询` 目录导入数据：

```bat
python init_db.py
```

看到 `导入完成：organic 表共有 271 条记录。` 即表示数据库准备完成。

### 2. 检查数据库配置

`config.py` 中保存数据库连接信息，密码从环境变量 `WEB_DB_PASSWORD` 读取（仓库中不保存密码）：

```python
import os

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "web",
    "password": os.environ.get("WEB_DB_PASSWORD", ""),
    "database": "web",
    "charset": "utf8mb4",
}
```

运行前先设置（PowerShell）：

```powershell
$env:WEB_DB_PASSWORD = "你的数据库密码"
```

> MySQL 8.0 默认的 `caching_sha2_password` 认证需要额外安装 cryptography，因此 `sql/setup.sql` 给项目账号 `web` 使用 `mysql_native_password` 认证，只装 PyMySQL 就能连接。

### 3. 启动网站

双击 `run.bat`，或在命令行执行：

```bat
cd 网站4-前后端查询
python app.py 8080
```

浏览器打开 <http://127.0.0.1:8080/>。

> 注意：必须通过 Web.py 服务访问页面（地址以 `http://127.0.0.1:8080` 开头）。如果直接双击 templates 中的模板文件，页面拿不到后端数据和样式。

## 五、实验要点

1. **前后端连接**：查询表单使用 GET 提交到 `/organic.html`，Web.py 的 `web.input()` 接收 `q`（关键词）和 `field`（查询字段）两个参数。
2. **数据库连接**：`pymysql.connect()` 建立连接，`fetch_all / fetch_one` 统一执行 SQL 并返回字典结果。
3. **参数化查询**：关键词通过 `%s` 占位符传入，字段名使用白名单映射，避免 SQL 注入。
4. **数据清洗**：数据库中的 NULL/空字符串在页面上显示为 `-`，模板只负责渲染。
5. **异常处理**：数据库未启动时页面显示提示信息而不是崩溃，方便检查环境。
6. **后端计算日历**：日历不再由 JavaScript 生成，而是后端使用 Python `calendar` 模块计算每周日期，再渲染成表格。

## 六、常见问题

- **`Access denied for user 'web'@'localhost'`**：没有执行 `sql/setup.sql` 或账号密码与 `config.py` 不一致。
- **`Unknown database 'web'`**：数据库还没有创建，先执行 `sql/setup.sql`。
- **页面 500 / 模板报错**：确认是通过 `python app.py 8080` 启动，并且 `templates`、`static` 目录与 `app.py` 在同一级。
- **8080 端口被占用**：换一个端口启动，例如 `python app.py 8090`。
- **中文显示乱码**：数据库和数据表统一使用 `utf8mb4`，CSV 使用 UTF-8 编码导入。
