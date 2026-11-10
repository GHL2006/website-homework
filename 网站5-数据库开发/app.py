# -*- coding: utf-8 -*-
"""网站5：数据库开发（基于通用模板 index.py 改写）。

功能：
    1. 登录 / 退出（web.session 保存登录状态）
    2. 英雄联盟棋子属性查询（MySQL 查询）
    3. 字典查询 + 查询记录（查询结果写入数据库）
    4. LOL 可视化：按卡费绘制棋子生命值柱状图（ECharts + JSON 接口）

运行：
    python app.py 8080
    浏览器打开 http://127.0.0.1:8080/
"""
from __future__ import print_function

import hashlib
import json
import os
import sys
import tempfile
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(os.path.dirname(BASE_DIR), ".deps")

# 优先使用 pip 安装的 web.py / PyMySQL，没有安装时使用项目自带的 .deps
try:
    import web  # noqa: F401
    import pymysql  # noqa: F401
except ImportError:
    if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
        sys.path.insert(0, VENDOR_DIR)
    import web  # noqa: F401
    import pymysql  # noqa: F401

os.chdir(BASE_DIR)
from pymysql.cursors import DictCursor  # noqa: E402

from config import DB_CONFIG  # noqa: E402

web.config.debug = False
render = web.template.render(os.path.join(BASE_DIR, "templates"))


# ---------------------------------------------------------------------------
# 数据库函数（对应通用模板的 sqlSelect / sqlWrite）
# ---------------------------------------------------------------------------
def get_connection():
    return pymysql.connect(cursorclass=DictCursor, autocommit=True, **DB_CONFIG)


def fetch_all(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=None):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.lastrowid
    finally:
        conn.close()


def count_table(table):
    row = fetch_one("SELECT COUNT(*) AS total FROM `%s`" % table)
    return int(row["total"]) if row else 0


def db_error_message(exc):
    return "数据库操作失败：%s（请确认 MySQL80 服务已启动、config.py 配置正确）" % exc


# ---------------------------------------------------------------------------
# 登录 / session 相关
# ---------------------------------------------------------------------------
def require_login():
    if not session.get("username"):
        raise web.seeother("/login.html")


def hash_password(password):
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()


def user_info():
    return {
        "username": session.get("username"),
        "display_name": session.get("display_name") or session.get("username"),
    }


# ---------------------------------------------------------------------------
# 页面处理类
# ---------------------------------------------------------------------------
class LoginPage:
    def GET(self):
        if session.get("username"):
            raise web.seeother("/index.html")
        return render.login(error=None, username="")

    def POST(self):
        data = web.input(username="", password="")
        username = (data.username or "").strip()
        password = data.password or ""
        if not username or not password:
            return render.login(error="请输入用户名和密码", username=username)
        row = fetch_one(
            "SELECT * FROM sys_user WHERE username=%s AND password_hash=%s",
            (username, hash_password(password)),
        )
        if not row:
            return render.login(error="用户名或密码错误", username=username)
        session.username = row["username"]
        session.display_name = row["display_name"] or row["username"]
        raise web.seeother("/index.html")


class LogoutPage:
    def GET(self):
        session.kill()
        raise web.seeother("/login.html")


class IndexPage:
    def GET(self):
        require_login()
        info = user_info()
        stats = {"champions": 0, "words": 0, "logs": 0}
        error = None
        try:
            stats["champions"] = count_table("lol_champion")
            stats["words"] = count_table("dict_word")
            stats["logs"] = count_table("dict_query_log")
        except Exception as exc:
            error = db_error_message(exc)
            traceback.print_exc()
        return render.index(user=info, stats=stats, error=error)


class LolPage:
    def GET(self):
        require_login()
        data = web.input(q="", price="all", job="all")
        keyword = (data.q or "").strip()
        price = data.price or "all"
        job = data.job or "all"
        if price not in (["all"] + [str(i) for i in range(0, 9)]):
            price = "all"

        where, params = [], []
        if keyword:
            where.append("(name LIKE %s OR title LIKE %s OR jobs LIKE %s OR races LIKE %s)")
            like = "%" + keyword + "%"
            params.extend([like, like, like, like])
        if price != "all":
            where.append("price=%s")
            params.append(int(price))
        if job != "all":
            where.append("jobs LIKE %s")
            params.append("%" + job + "%")
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""

        rows, total, error = [], 0, None
        try:
            total = int(fetch_one(
                "SELECT COUNT(*) AS total FROM lol_champion" + where_sql, params)["total"])
            rows = fetch_all(
                "SELECT * FROM lol_champion" + where_sql +
                " ORDER BY price, life DESC, id LIMIT 60", params)
            for row in rows:
                row["name"] = row["name"] or "—"
                for field in ("title", "jobs", "races", "skill_name", "skill_type"):
                    row[field] = row[field] or "—"
        except Exception as exc:
            error = db_error_message(exc)
            traceback.print_exc()

        job_options = []
        try:
            for item in fetch_all("SELECT jobs FROM lol_champion"):
                for name in (item["jobs"] or "").split(","):
                    name = name.strip()
                    if name and name not in job_options:
                        job_options.append(name)
            job_options.sort()
        except Exception:
            pass

        return render.lol(
            user=user_info(), rows=rows, total=total, keyword=keyword,
            price=price, job=job, job_options=job_options, error=error)


class DictPage:
    def GET(self):
        require_login()
        data = web.input(q="")
        keyword = (data.q or "").strip()
        rows, logs, error = [], [], None
        try:
            if keyword:
                rows = fetch_all(
                    "SELECT * FROM dict_word WHERE word LIKE %s OR translation LIKE %s"
                    " ORDER BY id LIMIT 20",
                    ("%" + keyword + "%", "%" + keyword + "%"))
                execute(
                    "INSERT INTO dict_query_log (username, keyword, result_count)"
                    " VALUES (%s, %s, %s)",
                    (session.get("username"), keyword, len(rows)))
            logs = fetch_all(
                "SELECT * FROM dict_query_log ORDER BY id DESC LIMIT 10")
        except Exception as exc:
            error = db_error_message(exc)
            traceback.print_exc()
        return render.dict(
            user=user_info(), rows=rows, logs=logs, keyword=keyword,
            searched=bool(keyword), error=error)


class ChartPage:
    def GET(self):
        require_login()
        return render.chart(user=user_info(), price_options=PRICE_OPTIONS)


class ApiChart:
    """GET /api/chart?price=1 返回该卡费全部棋子的生命值 JSON。"""

    def GET(self):
        if not session.get("username"):
            web.header("Content-Type", "application/json; charset=utf-8")
            web.ctx.status = "401 Unauthorized"
            return json.dumps({"error": "login required"}, ensure_ascii=False)
        try:
            price = int(web.input(price="1").price)
        except (TypeError, ValueError):
            price = 1
        if price < 0 or price > 8:
            price = 1
        rows = fetch_all(
            "SELECT id, name, life, price FROM lol_champion WHERE price=%s"
            " ORDER BY life DESC, id", (price,))
        result = {
            "price": price,
            "count": len(rows),
            "names": [row["name"] for row in rows],
            "lives": [row["life"] for row in rows],
            "ids": [row["id"] for row in rows],
            "average": round(sum(row["life"] for row in rows) / len(rows), 1) if rows else 0,
        }
        web.header("Content-Type", "application/json; charset=utf-8")
        web.header("Cache-Control", "no-store")
        return json.dumps(result, ensure_ascii=False)


PRICE_OPTIONS = [
    (str(i), "%d 费" % i) for i in range(1, 9)
] + [("0", "0 费（召唤物）")]


urls = (
    "/", "IndexPage",
    "/index.html", "IndexPage",
    "/login.html", "LoginPage",
    "/logout.html", "LogoutPage",
    "/lol.html", "LolPage",
    "/dict.html", "DictPage",
    "/chart.html", "ChartPage",
    "/api/chart", "ApiChart",
)

app = web.application(urls, globals())
session = web.session.Session(
    app,
    web.session.DiskStore(tempfile.mkdtemp()),
    initializer={"username": None, "display_name": None},
)


def serve_with_builtin_wsgi(port):
    """没有 cheroot 时用 Python 自带的 wsgiref 多线程服务器启动。"""
    from socketserver import ThreadingMixIn
    from wsgiref.simple_server import WSGIServer, make_server

    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        daemon_threads = True

    wsgi_app = app.wsgifunc(web.httpserver.StaticMiddleware)
    httpd = make_server("0.0.0.0", port, wsgi_app, server_class=ThreadingWSGIServer)
    print("http://127.0.0.1:%d/" % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    try:
        app.run(web.httpserver.StaticMiddleware)
    except ImportError:
        port = 8080
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                port = 8080
        serve_with_builtin_wsgi(port)
