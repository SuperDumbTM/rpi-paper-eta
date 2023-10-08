from enum import Enum


class FlashCategory(str, Enum):
    info = "info"
    success = "success"
    warn = "warning"
    error = "error"
