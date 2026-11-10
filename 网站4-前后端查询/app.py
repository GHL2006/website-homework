# -*- coding: utf-8 -*-
"""网站设计与开发实验：前后端连接 + MySQL 数据库查询。

运行方式：
    python app.py 8080
然后在浏览器中访问 http://127.0.0.1:8080/

页面：
    /index.html      主页（本月日历由后端计算）
    /calendar.html   日历查询（Web.py 后端计算并渲染）
    /organic.html    有机物查询（数据来自 MySQL 数据库 web.organic）
    /resume.html     个人简历
    /bootstrap.html  Bootstrap 组件样例
"""
from __future__ import print_function

import calendar
import datetime as dt
import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(os.path.dirname(BASE_DIR), ".deps")

# 优先使用 pip 安装的 web.py / PyMySQL；没有安装时再使用项目自带的 .deps，
# 保证「pip install web.py pymysql」和「直接复制项目」两种方式都能运行。
try:
    import web  # noqa: F401
    import pymysql  # noqa: F401
except ImportError:
    if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
        sys.path.insert(0, VENDOR_DIR)
    import web  # noqa: F401
    import pymysql  # noqa: F401

# StaticMiddleware 需要以项目目录为工作目录才能找到 /static/ 下的文件
os.chdir(BASE_DIR)

from pymysql.cursors import DictCursor  # noqa: E402

from config import DB_CONFIG, MAX_RESULT_ROWS, ORGANIC_TABLE  # noqa: E402

web.config.debug = False

render = web.template.render(
    os.path.join(BASE_DIR, "templates"),
    globals={"len": len, "enumerate": enumerate},
)

WEEKDAY_NAMES = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
MONTH_NAMES_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTH_OPTIONS = [(number, "%d 月" % number) for number in range(1, 13)]
FIELD_OPTIONS = [
    ("all", "全部字段"),
    ("name", "名称"),
    ("formula", "分子式"),
    ("cas", "CAS 号"),
]
FIELD_COLUMNS = {"name": "name", "formula": "formula", "cas": "cas"}

# 首页与日历页面的默认年月：与实验参考结果保持一致（2022 年 8 月）
DEFAULT_YEAR = 2022
DEFAULT_MONTH = 8


# --------------------------------------------------------------------------
# 数据库相关函数
# --------------------------------------------------------------------------
def get_connection():
    """创建一个新的数据库连接（每次请求用完即关闭）。"""
    return pymysql.connect(cursorclass=DictCursor, autocommit=True, **DB_CONFIG)


def fetch_all(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=None):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def clean_value(value, fallback="-"):
    """数据库中的空值在页面上显示为 -。"""
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def clean_name(value):
    """名称字段：为空时显示 -（正常情况下都有名称）。"""
    return clean_value(value)


def count_records():
    """统计有机物表中的数据总条数，用来在页面上展示数据库来源。"""
    row = fetch_one("SELECT COUNT(*) AS total FROM %s" % ORGANIC_TABLE)
    return int(row["total"]) if row else 0


def search_organic(keyword, field):
    """根据关键词和字段从 MySQL 中查询有机物。

    使用参数化查询（%s）防止 SQL 注入；字段名使用白名单映射，
    不能把用户输入直接拼进 SQL。
    """
    keyword = (keyword or "").strip()
    if field not in FIELD_COLUMNS and field != "all":
        field = "all"

    where_sql = ""
    params = []
    if keyword:
        like_value = "%" + keyword + "%"
        if field == "all":
            where_sql = (
                " WHERE name LIKE %s OR formula LIKE %s OR cas LIKE %s"
            )
            params = [like_value, like_value, like_value]
        else:
            where_sql = " WHERE " + FIELD_COLUMNS[field] + " LIKE %s"
            params = [like_value]

    total_row = fetch_one(
        "SELECT COUNT(*) AS total FROM %s%s" % (ORGANIC_TABLE, where_sql),
        params,
    )
    total_matches = int(total_row["total"]) if total_row else 0

    rows = fetch_all(
        "SELECT id, name, formula, cas, molecular_weight, boilling_point "
        "FROM %s%s ORDER BY id LIMIT %d" % (ORGANIC_TABLE, where_sql, MAX_RESULT_ROWS),
        params,
    )
    cleaned_rows = []
    for row in rows:
        cleaned_rows.append(
            {
                "id": row["id"],
                "name": clean_name(row["name"]),
                "formula": clean_value(row["formula"]),
                "cas": clean_value(row["cas"]),
                "molecular_weight": clean_value(row["molecular_weight"]),
                "boilling_point": clean_value(row["boilling_point"]),
            }
        )
    return total_matches, cleaned_rows


# --------------------------------------------------------------------------
# 日历相关函数
# --------------------------------------------------------------------------
def normalize_year_month(year, month):
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = DEFAULT_YEAR
    try:
        month = int(month)
    except (TypeError, ValueError):
        month = DEFAULT_MONTH
    if year < 1900 or year > 2100:
        year = DEFAULT_YEAR
    if month < 1 or month > 12:
        month = DEFAULT_MONTH
    return year, month


def build_calendar(year, month):
    """返回该月按星期一分栏的日期表，每行 7 个数字，0 表示空白格。"""
    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    return weeks


def build_month_info(year, month):
    month_name = MONTH_NAMES_EN[month - 1]
    return {
        "month_name": month_name,
        "month_title": "%s %d" % (month_name, year),
    }


def database_error_message(exc):
    return (
        "数据库连接或查询失败：%s。请确认 MySQL80 服务已启动，"
        "并检查 webapp/config.py 中的数据库账号和密码。" % exc
    )


# --------------------------------------------------------------------------
# 页面控制器
# --------------------------------------------------------------------------
class IndexPage:
    """主页：展示本月日历预览和功能入口。"""

    def GET(self):
        today = dt.date.today()
        year, month = today.year, today.month
        info = build_month_info(year, month)
        total_records, db_ok, db_message = 0, True, ""
        try:
            total_records = count_records()
        except Exception as exc:  # 数据库不可用时页面仍然可以打开
            db_ok = False
            db_message = database_error_message(exc)
            traceback.print_exc()
        return render.index(
            year=year,
            month=month,
            month_name_en=info["month_name"],
            weeks=build_calendar(year, month),
            total_records=total_records,
            db_ok=db_ok,
            db_message=db_message,
        )


class CalendarPage:
    """日历页面：由后端计算月历，再交给模板渲染。"""

    def GET(self):
        data = web.input(year=None, month=None)
        year, month = normalize_year_month(data.year, data.month)
        info = build_month_info(year, month)
        today = dt.date.today()
        return render.calendar(
            year=year,
            month=month,
            weeks=build_calendar(year, month),
            month_title=info["month_title"],
            today_year=today.year,
            today_month=today.month,
            month_options=MONTH_OPTIONS,
        )


class OrganicPage:
    """有机物查询页面：关键词提交给 Web.py，由后端执行 SQL 查询 MySQL。"""

    def GET(self):
        data = web.input(q="甲醛", field="all")
        keyword = (data.q or "").strip()
        field = data.field or "all"
        if field not in FIELD_COLUMNS and field != "all":
            field = "all"

        total_records = 0
        total_matches = 0
        rows = []
        db_ok = True
        db_message = ""
        try:
            total_records = count_records()
            total_matches, rows = search_organic(keyword, field)
        except Exception as exc:
            db_ok = False
            db_message = database_error_message(exc)
            traceback.print_exc()

        return render.organic(
            rows=rows,
            total_matches=total_matches,
            keyword=keyword,
            field=field,
            total_records=total_records,
            db_ok=db_ok,
            db_message=db_message,
            field_options=FIELD_OPTIONS,
        )

    POST = GET


class ResumePage:
    def GET(self):
        return render.resume()


class BootstrapPage:
    def GET(self):
        return render.bootstrap()


urls = (
    "/", "IndexPage",
    "/index.html", "IndexPage",
    "/calendar.html", "CalendarPage",
    "/organic.html", "OrganicPage",
    "/resume.html", "ResumePage",
    "/bootstrap.html", "BootstrapPage",
)

app = web.application(urls, globals())


def serve_with_builtin_wsgi(port):
    """在没有安装 cheroot 时，用 Python 自带的 wsgiref 多线程服务器启动。

    web.py 0.62 的 app.run() 依赖 cheroot，本实验项目为了脱离外网安装，
    自带一个基于标准库的 WSGI 服务器作为兜底，页面和 /static/ 静态文件
    的访问方式与 app.run() 完全一致。
    """
    from socketserver import ThreadingMixIn
    from wsgiref.simple_server import WSGIServer, make_server

    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        daemon_threads = True

    wsgi_app = app.wsgifunc(web.httpserver.StaticMiddleware)
    httpd = make_server(
        "0.0.0.0", port, wsgi_app, server_class=ThreadingWSGIServer
    )
    print("http://127.0.0.1:%d/" % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    # 运行：python app.py 8080
    try:
        app.run(web.httpserver.StaticMiddleware)
    except ImportError:
        # 当前环境没有 cheroot，改用标准库 wsgiref 服务器
        port = 8080
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                port = 8080
        serve_with_builtin_wsgi(port)

