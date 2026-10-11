"""Upload tests: real type check, size limit, EXIF removal."""
import io
import re

import pytest
from PIL import Image

from app import config
from app.vision.review import ImageRejected, sanitize_image


def _jpeg_with_exif() -> bytes:
    img = Image.new("RGB", (640, 480), (80, 140, 70))
    exif = Image.Exif()
    exif[0x010F] = "TestCamera"         # Make
    exif[0x010E] = "secret location"    # ImageDescription
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif)
    return buf.getvalue()


def test_text_file_renamed_jpg_is_rejected(client):
    r = client.post("/upload", files={"file": ("crop.jpg", b"just some text", "image/jpeg")})
    assert r.status_code == 400


def test_oversize_file_is_rejected(client):
    big = b"\xff\xd8\xff" + b"0" * (config.MAX_UPLOAD_BYTES + 10)
    assert client.post("/upload", files={"file": ("big.jpg", big, "image/jpeg")}).status_code == 413


def test_exif_is_removed_from_stored_file(client):
    data = _jpeg_with_exif()
    assert len(Image.open(io.BytesIO(data)).getexif()) > 0  # the input really had EXIF
    r = client.post("/upload", files={"file": ("photo.jpg", data, "image/jpeg")})
    assert r.status_code == 200
    name = re.search(r"/uploads/([0-9a-f]{32}\.jpg)", r.text).group(1)
    stored = Image.open(config.upload_dir() / name)
    assert len(stored.getexif()) == 0
    assert client.get(f"/uploads/{name}").status_code == 200


def test_uploads_folder_is_not_listable(client):
    assert client.get("/uploads/").status_code in (404, 405)
    assert client.get("/uploads/not-a-real-name.jpg").status_code == 404


def test_sanitize_rejects_garbage_directly():
    with pytest.raises(ImageRejected):
        sanitize_image(b"GIF89a-not-really")
