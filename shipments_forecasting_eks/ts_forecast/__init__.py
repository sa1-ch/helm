try:
    from ._version import version
except Exception:
    try:
        from setuptools_scm import get_version

        version = get_version()
    except Exception:
        version = "???"

__version__ = version
