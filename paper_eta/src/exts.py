from flask_apscheduler import APScheduler
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy

from paper_eta.src.libs import hketa as hketa_

db = SQLAlchemy()

scheduler = APScheduler()

babel = Babel()

hketa = hketa_.EtaFactory()
