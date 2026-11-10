# 网站5：数据库开发（英雄联盟棋子数据库系统）

基于老师提供的通用模板 `index.py` 改写，使用 **Web.py + PyMySQL + MySQL 8.0 + Bootstrap 3.3.7 + ECharts** 完成《网站设计与开发》实验五「数据库开发」。

## 功能

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 登录 | `/login.html` | 用户名密码登录，登录状态保存在 Web.py session 中 |
| 主页 | `/index.html` | 功能入口 + 数据库统计（棋子 / 字典 / 查询记录条数） |
| 棋子查询 | `/lol.html` | 按关键词、卡费、职业查询 `lol_champion` 表，展示头像与属性 |
| 字典查询 | `/dict.html` | 查询 `dict_word` 表，每次查询写入 `dict_query_log` 表并显示最近记录 |
| 数据可视化 | `/chart.html` | 选择卡费，ECharts 柱状图展示相同卡费棋子的生命值 |
| 图表接口 | `/api/chart?price=1` | 返回指定卡费的棋子名称与生命值 JSON |

未登录访问除登录页以外的页面会自动跳转到 `/login.html`。

## 数据库设计（数据库 `web`）

| 表 | 说明 | 初始数据 |
| --- | --- | --- |
| `lol_champion` | 英雄联盟棋子属性（id= TFTID，含名称、卡费、生命值、攻击、护甲、魔抗、职业、种族、技能、图片等） | 86 条 |
| `dict_word` | 字典词条（单词、音标、中文释义） | 66 条 |
| `dict_query_log` | 字典查询记录（用户名、关键词、结果数、查询时间） | 0 条（查询时写入） |
| `sys_user` | 登录用户（用户名、sha256 密码哈希、显示名） | 2 条 |

数据来源：

- `data/lol.csv`：由老师提供的 `lol.csv`（GBK 编码）转为 UTF-8，共 86 个棋子；
- `data/dict_words.csv`：字典词条数据；
- `static/lol/*.jpg`：由老师提供的 `lol图片.zip` 解压得到（64 张，22 个召唤物无图，页面显示“无图”）。

## 运行步骤

1. 启动 MySQL80 服务（数据库 `web`、账号 `web`，密码通过环境变量 `WEB_DB_PASSWORD` 传入，仓库中不保存密码）。
2. 设置环境变量（PowerShell）：

   ```powershell
   $env:WEB_DB_PASSWORD = "你的数据库密码"
   ```

3. 初始化数据（只需执行一次）：

   ```bat
   cd 网站5-数据库开发
   python init_db.py
   ```

   看到 `lol_champion 86 条 / dict_word 66 条 / sys_user 2 条` 即成功。

3. 启动网站：

   ```bat
   cd 网站5-数据库开发
   python app.py 8080
   ```

   或双击 `run.bat`，然后浏览器打开 <http://127.0.0.1:8080/>。

4. 使用示例账号登录：`admin / 123456` 或 `student / 123456`。

## 代码结构

```
网站5-数据库开发/
├── app.py            Web.py 路由、session 登录、数据库查询、/api/chart 接口
├── config.py         MySQL 连接配置
├── init_db.py        建表 + 导入 lol.csv / 字典 / 用户数据
├── run.bat           Windows 一键启动
├── data/
│   ├── lol.csv       棋子数据（UTF-8）
│   └── dict_words.csv 字典数据
├── static/
│   ├── bootstrap.min.css / jquery.min.js / bootstrap.min.js
│   ├── echarts.js    图表库
│   ├── site.css      自定义样式
│   └── lol/          棋子头像（按 TFTID 命名，如 783.jpg）
└── templates/
    ├── login.html
    ├── index.html
    ├── lol.html
    ├── dict.html
    └── chart.html
```

## 和通用模板的对应关系

| 通用模板 | 本项目 |
| --- | --- |
| `urls` 路由表 | 扩展成登录、主页、棋子、字典、图表、图表接口 8 条路由 |
| `class index: GET / POST` | `LoginPage` / `IndexPage` / `LolPage` / `DictPage` / `ChartPage` / `ApiChart` |
| `render = web.template.render('templates/')` | 保留，模板增加登录页等 5 个文件 |
| `sqlSelect` / `sqlWrite` | 升级为 `fetch_all` / `fetch_one` / `execute`，使用 DictCursor 和参数化查询 |
| `session = web.session.Session(...)` | 保留并用于登录状态保存（`session.username`） |
| `web.config.debug = False`、`app.run()` | 保留 |
