from datasette.app import Datasette
from datasette import hookimpl
from datasette.plugins import pm
from functools import wraps
import pytest


class ContentModifyingPlugin:
    __name__ = "ContentModifyingPlugin"

    @hookimpl
    def asgi_wrapper(self):
        def wrap_with_content_modify(app):
            print("wrap_with_content_modify")

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
    pm.register(ContentModifyingPlugin(), name="undo")
    try:
        datasette = Datasette([], memory=True)
        response = await datasette.client.get("/_memory?sql=select+zeroblob%2810000%29")
        assert "<HTML>" in response.text
    finally:
        pm.unregister(name="undo")
