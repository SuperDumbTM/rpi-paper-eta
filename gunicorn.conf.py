wsgi_app = "paper_eta.main:create_app()"
proc_name = "rpi-paper-eta"
bind = "0.0.0.0:8192"
threads = 4
worker_class = "gthread"
timeout = 90
accesslog = "-"
