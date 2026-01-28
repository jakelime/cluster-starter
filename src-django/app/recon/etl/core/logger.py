import logging
import logging.config
import os
from pathlib import Path

# --- 1. Define Application Constants and Paths ---

# Define the name of your standalone application
APP_NAME = "mctr"

# Check environment variable for log root
_LOG_DIRPATH = os.getenv("DJANGO_LOGS_ROOT", "")

# Determine the final log directory path using pattern matching
match _LOG_DIRPATH:
    # Case 1: Environment variable contains a home path (e.g., "~/my_logs")
    case x if "~" in x:
        # Expand user path, but do not append APP_NAME if the path is explicit
        LOG_DIRPATH = Path(x).expanduser()
    # Case 2: Environment variable is empty, use the default home directory path
    case "":
        # Default path is $HOME/logs/mctr
        LOG_DIRPATH = Path("~").expanduser() / "logs" / APP_NAME
    # Case 3: Environment variable contains a full, absolute path
    case _:
        LOG_DIRPATH = Path(_LOG_DIRPATH)

# Ensure the log directory exists
if not LOG_DIRPATH.is_dir():
    LOG_DIRPATH.mkdir(parents=True, exist_ok=True)

# Define the full path for the log file
LOGFILE_FILEPATH = LOG_DIRPATH / "app-logs.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(name)s:%(levelname)s:%(asctime)s.%(msecs)03d:%(module)s: %(message)s",
            "style": "%",
            "datefmt": "%Y%m%d_%H%M%S",
        },
        "simple": {
            "format": "%(levelname)s: %(message)s",
            "style": "%",
        },
    },
    "handlers": {
        # File handler uses TimedRotatingFileHandler for daily log rotation
        "file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            # Use the absolute path for the log file
            "filename": f"{LOGFILE_FILEPATH.absolute()}",
            "formatter": "verbose",
            "when": "D",  # Rotate daily
            "interval": 1,  # Every 1 day
            "backupCount": 365,  # Keep 365 log files
            "utc": True,  # Use UTC time for log timestamps/rotation
        },
        # Console handler prints to stdout/stderr
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        # Optional: Configure the root logger
        "": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
        },  # Configured logger that handles file and console output
    },
}

# Global flag to ensure configuration is loaded only once
_LOGGING_INITIALIZED = False


def getLogger(name: str):
    global _LOGGING_INITIALIZED
    if not _LOGGING_INITIALIZED:
        logging.config.dictConfig(LOGGING_CONFIG)
        _LOGGING_INITIALIZED = True
    return logging.getLogger(name)
