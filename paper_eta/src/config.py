import os
from pathlib import Path
import random
import shutil
import string
import dotenv

__APP_ROOT = Path(__file__).parents[1]
__PATH_ENV = __APP_ROOT.parent.joinpath('.env')

dotenv.load_dotenv(__PATH_ENV)

# app paths
DIR_STORAGE = Path(os.getenv('DIR_STORAGE', __APP_ROOT.joinpath('storage')))
DIR_SCREEN_DUMP = Path(
    os.getenv('DIR_SCREEN_DUMP', DIR_STORAGE.joinpath('screen_dumps')))
PATH_LOG_FILE = Path(
    os.getenv('PATH_LOG_FILE', DIR_STORAGE).joinpath('app.log'))
PATH_SITE_CONF = Path(
    os.getenv('PATH_SITE_CONF', DIR_STORAGE).joinpath('config.json'))

# app settings
ENV = os.getenv('ENV', 'development')
DEBUG = (ENV == 'development')
SECRET_KEY = os.getenv('SECRET_KEY')

if not SECRET_KEY:
    # presist the newly created secret key
    SECRET_KEY = ' '.join(random.SystemRandom()
                          .choice(string.ascii_uppercase + string.digits)
                          for _ in range(64))
    if not __PATH_ENV.exists():
        shutil.copy(f'{__PATH_ENV.name}.sample', __PATH_ENV)
    dotenv.set_key(__PATH_ENV, 'SECRET_KEY', SECRET_KEY)

# Bable
BABEL_TRANSLATION_DIRECTORIES = str(__APP_ROOT.joinpath("translations"))
BABEL_DEFAULT_LOCALE = os.getenv('BABEL_DEFAULT_LOCALE', 'en')
BABEL_DEFAULT_TIMEZO = os.getenv('BABEL_DEFAULT_TIMEZO', 'Asia/Hong_kong')

# sqlalchemy
SQLALCHEMY_DATABASE_URI = os.getenv(
    'SQLALCHEMY_DATABASE_URI', "sqlite:///{}".format(DIR_STORAGE.joinpath('app.db')))

# hketa
HKETA_PATH_DATA = Path(
    os.getenv('HKETA_PATH_DATA', DIR_STORAGE).joinpath('hketa'))
HKETA_THRESHOLD = int(os.getenv('HKETA_THRESHOLD', 30))

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'print': {
            'format': '[%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        },
        'detailed': {
            'format': '[%(asctime)s][%(levelname)s][%(name)s.%(module)s]: %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        },
    },
    'handlers': {
        'wsgi': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'print',
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "print",
            "stream": "ext://sys.stdout",
        },
        'size-rotate': {
            'level': 'DEBUG',
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 524288,
            "backupCount": 1,
            "filename": PATH_LOG_FILE,
            'encoding': 'utf-8',
            "formatter": "detailed",
        },
    },
    'loggers': {
        "gunicorn.error": {
            "handlers": ['console', 'size-rotate'],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": ["console"] if DEBUG else ['console', 'size-rotate'],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi', 'size-rotate']
    },
}
