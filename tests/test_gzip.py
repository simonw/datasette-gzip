from functools import wraps

import httpx
import pytest
from datasette import hookimpl
from datasette.app import Datasette
from datasette.plugins import pm
from starlette.middleware.gzip import GZipMiddleware

import datasette_gzip


class ContentModifyingPlugin:
    __name__ = "ContentModifyingPlugin"

    @hookimpl
    def asgi_wrapper(self):
        def wrap_with_content_modify(app):
            @wraps(app)
            async def modify_content(scope, receive, send):
                async def wrapped_send(event):
                    if event["type"] == "http.response.body" and event.get("body"):
                        event["body"] = event["body"].upper()
                    await send(event)

                await app(scope, receive, wrapped_send)

            return modify_content

        return wrap_with_content_modify


@pytest.mark.asyncio
async def test_accept_gzip_makes_a_difference():
    datasette = Datasette([], memory=True)
    response = await datasette.client.get(
        "/_memory.json?sql=select+zeroblob%2810000%29",
        headers={"Accept-Encoding": "identity"},
    )
    assert response.status_code == 200
    original_length = len(response.text)
    original_bytes_downloaded = response.num_bytes_downloaded
    assert original_bytes_downloaded == original_length
    assert original_length > 50000
    # Now try with accept: gzip (the default for client.get())
    gzip_response = await datasette.client.get(
        "/_memory.json?sql=select+zeroblob%2810000%29"
    )
    gzip_length_after_decompression = len(gzip_response.text)
    gzip_bytes_downloaded = gzip_response.num_bytes_downloaded
    assert gzip_length_after_decompression > gzip_bytes_downloaded
    assert gzip_length_after_decompression > 50000
    assert gzip_bytes_downloaded < 10000


@pytest.mark.asyncio
async def test_compatible_with_plugins_that_modify_content():
    pm.register(ContentModifyingPlugin(), name="content_modifying")
    try:
        datasette = Datasette([], memory=True)
        response = await datasette.client.get("/_memory?sql=select+zeroblob%2810000%29")
        assert "<HTML>" in response.text
    finally:
        pm.unregister(name="content_modifying")


class GzipTryFirst:
    __name__ = "GzipTryFirst"

    @hookimpl(tryfirst=True)
    def asgi_wrapper(self):
        return GZipMiddleware


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "plugin,should_work",
    (
        (datasette_gzip, True),
        (GzipTryFirst(), False),
    ),
)
async def test_trylast_true_is_what_makes_this_work(plugin, should_work):
    try:
        # First unregister the default gzip plugin
        original_gzip = pm.unregister(name="gzip")
        pm.register(ContentModifyingPlugin(), name="content_modifying")
        # Register new gzip plugin, which will be tryfirst or trylast:
        pm.register(plugin, name="gzip")
        datasette = Datasette([], memory=True)
        if should_work:
            response = await datasette.client.get(
                "/_memory?sql=select+zeroblob%2810000%29"
            )
            assert "<HTML>" in response.text
        else:
            # If plugins execute in incorrect order we should get a gzip error
            with pytest.raises(httpx.DecodingError):
                await datasette.client.get("/_memory?sql=select+zeroblob%2810000%29")
    finally:
        pm.unregister(name="gzip")
        pm.unregister(name="content_modifying")
        pm.register(original_gzip, name="gzip")
