from datasette import hookimpl
from starlette.middleware.gzip import GZipMiddleware


@hookimpl(trylast=True)
def asgi_wrapper(datasette):
    return GZipMiddleware
