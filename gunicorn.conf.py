wsgi_app = "paper_eta.main:create_app()"
proc_name = "rpi-paper-eta"
bind = "0.0.0.0:8192"
workers = 2
worker_class = "sync"
timeout = 90
accesslog = "-"
preload_app = True
