from datasette.app import Datasette
import pytest


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
