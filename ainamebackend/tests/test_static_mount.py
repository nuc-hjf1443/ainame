from starlette.routing import Mount

from main import app


def test_only_visual_uploads_are_publicly_mounted():
    mount_paths = [route.path for route in app.routes if isinstance(route, Mount)]
    assert "/uploads/visuals" in mount_paths
    assert "/uploads" not in mount_paths
