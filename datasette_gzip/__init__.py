from datasette import hookimpl
from asgi_gzip import GZipMiddleware


@hookimpl(trylast=True)
def asgi_wrapper(datasette):
    return GZipMiddleware
