from inndxd_api.main import create_app


def test_runs_router_exists():
    """Test that the runs router is registered."""
    app = create_app()
    routes = [route.path for route in app.routes]
    assert any("/api/runs/{brief_id}" in route for route in routes)


def test_create_app_returns_fastapi_instance():
    """Test that create_app returns a FastAPI instance."""
    from fastapi import FastAPI

    app = create_app()
    assert isinstance(app, FastAPI)
