from pathlib import Path

from fastapi.testclient import TestClient

from dungeon_master.api.app import create_app


def test_health_route_answers(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "no-build"))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_built_client_is_served_from_the_root(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<p>the table</p>")
    client = TestClient(create_app(tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "the table" in response.text


def test_api_is_not_shadowed_by_the_client(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<p>the table</p>")
    client = TestClient(create_app(tmp_path))

    response = client.get("/api/health")

    assert response.json() == {"status": "ok"}


def test_without_a_client_build_only_the_api_is_served(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "no-build"))

    assert client.get("/api/health").status_code == 200
    assert client.get("/").status_code == 404
