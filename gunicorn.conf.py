wsgi_app = "app.src.main:create_app()"
proc_name = "rpi-paper-eta"
bind = "0.0.0.0:8192"
workers = 1
worker_class = "sync"
timeout = 60
accesslog = "-"
