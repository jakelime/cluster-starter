from django.conf import settings


def get_git_version(*args, **kwargs):
    """function to get version number from settings.py

    :return: version string
    :rtype: str
    """
    return {"GIT_VERSION": settings.GIT_VERSION}


def is_development_environment(host) -> bool:
    if settings.IS_DEVELOPMENT:
        return {"IS_DEVELOPMENT": True}
    return {"IS_DEVELOPMENT": False}
