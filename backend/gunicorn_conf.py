"""
Gunicorn configuration for production deployment
FastAPI + Uvicorn workers for async support
"""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8001')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "portfolio-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = os.getenv('SSL_KEYFILE', None)
certfile = os.getenv('SSL_CERTFILE', None)

# Preload app for better performance
preload_app = True

# Graceful timeout for worker restart
graceful_timeout = 30

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Portfolio API server")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Portfolio API server")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"Portfolio API ready with {workers} workers")

def on_exit(server):
    """Called just before exiting the master process."""
    server.log.info("Shutting down Portfolio API server")
