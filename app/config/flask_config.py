from pathlib import Path


ENV_FILE_PATH = Path(__file__).parent.parent.parent.joinpath(".env")
"""Path to `.env` file"""

CONFIG_DIR = Path(__file__).parent.parent.joinpath("config", "data")
"""Path to the directory for configuration files"""

CACHE_DIR = Path(__file__).parent.parent.joinpath("caches")
"""Path to the directory for cache files"""

BABEL_TRANSLATION_DIRECTORIES = str(Path(
    __file__).parent.parent.parent.joinpath("translations"))
