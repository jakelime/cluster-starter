import os

from uvicorn.workers import UvicornWorker

SCRIPT_NAME = os.getenv("PROXY_PREFIX", "")

if SCRIPT_NAME:
    CONFIG_KWARGS = {
        "root_path": SCRIPT_NAME,
        "proxy_headers": True,
        "lifespan": "off",
    }
else:
    CONFIG_KWARGS = {"lifespan": "off"}


class DjangoUvicornWorker(UvicornWorker):
    """Uvicorn worker class for running Django applications with Gunicorn.
    Lifespan events are disabled because Django's `get_asgi_application()`
    tpyically only listens for HTTP and websocket (if configured).
    """

    CONFIG_KWARGS: dict = CONFIG_KWARGS
