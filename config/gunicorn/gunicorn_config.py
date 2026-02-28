"""
Gunicorn 配置文件 - 生产环境
"""

import multiprocessing
import os

# ============================================
# Server Socket
# ============================================
bind = "0.0.0.0:8000"
backlog = 2048

# ============================================
# Worker Processes
# ============================================
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# ============================================
# Security
# ============================================
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# ============================================
# Logging
# ============================================
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "/app/logs/gunicorn_access.log")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "/app/logs/gunicorn_error.log")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ============================================
# Process Naming
# ============================================
proc_name = "django_erp"

# ============================================
# Server Mechanics
# ============================================
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None


# ============================================
# Server Hooks
# ============================================
def on_starting(server):
    """在主进程启动前调用"""
    print("🚀 Gunicorn is starting...")


def on_reload(server):
    """在重新加载时调用"""
    print("🔄 Gunicorn is reloading...")


def when_ready(server):
    """在主进程完全启动后调用"""
    print("✅ Gunicorn is ready. Spawning workers...")


def pre_fork(server, worker):
    """在 fork worker 之前调用"""
    pass


def post_fork(server, worker):
    """在 fork worker 之后调用"""
    print(f"👷 Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """在重新执行之前调用"""
    print("🔧 Forked child, re-executing.")


def post_worker_init(worker):
    """在 worker 初始化之后调用"""
    print(f"✨ Worker initialized (pid: {worker.pid})")


def worker_int(worker):
    """在 worker 收到 INT 或 QUIT 信号时调用"""
    print(f"⚠️  Worker received INT or QUIT signal (pid: {worker.pid})")


def worker_abort(worker):
    """在 worker 收到 SIGABRT 信号时调用"""
    print(f"❌ Worker received SIGABRT signal (pid: {worker.pid})")
