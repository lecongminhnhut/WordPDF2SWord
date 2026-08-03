import os


bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "540"))
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
