from flask_apscheduler import APScheduler
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy

from .libs.hketa import factories

db = SQLAlchemy()

scheduler = APScheduler()

babel = Babel()

hketa = factories.EtaFactory()
