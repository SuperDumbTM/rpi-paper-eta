from pathlib import Path


CONFIG_DIR = Path(__file__).parent.parent.joinpath("config", "data")
"""Path to the directory for configuration files"""

CACHE_DIR = Path(__file__).parent.parent.joinpath("caches")
"""Path to the directory for cache files"""

ENV_FILE_PATH = Path(__file__).parent.parent.parent.joinpath(".env")
"""Path to `.env` file"""

LOG_FILE_PATH = CACHE_DIR.joinpath('app.log')
"""Path to app's log file"""

I18N = ['en', 'zh_Hant_HK']
"""List of locale name that the app supports for translation"""

# Flask Babel configuration

BABEL_TRANSLATION_DIRECTORIES = str(
    Path(__file__).parent.parent.parent.joinpath("translations"))
