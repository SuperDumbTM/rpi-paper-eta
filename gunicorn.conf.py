wsgi_app = "app.main:create_app()"
proc_name = "rpi-paper-eta"
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
timeout = 60
accesslog = "-"
