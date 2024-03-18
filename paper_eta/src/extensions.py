from flask_apscheduler import APScheduler
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

scheduler = APScheduler()

babel = Babel()
