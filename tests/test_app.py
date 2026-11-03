from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")

PAGES = [
    "Dashboard",
    "Robot Simulation",
    "Mission Management",
    "Mission History",
    "Robot Monitoring",
]


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return AppTest.from_file(APP_PATH, default_timeout=30).run()


def test_app_starts_without_errors(app):
    assert not app.exception


def test_dashboard_shows_metrics(app):
    labels = [metric.label for metric in app.metric]
    assert "Total Missions" in labels
    assert "Robot Status" in labels


def test_all_pages_render_without_errors(app):
    for page in PAGES:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, f"Error on page {page}"


def test_create_mission_from_form(app):
    app.sidebar.radio[0].set_value("Mission Management").run()
    app.selectbox[0].set_value("Pharmacy")
    app.selectbox[1].set_value("Laboratory")
    app.selectbox[2].set_value("High")
    app.button[0].click().run()
    assert not app.exception
    assert len(app.success) == 1


def test_same_start_and_destination_shows_error(app):
    app.sidebar.radio[0].set_value("Mission Management").run()
    app.selectbox[0].set_value("Pharmacy")
    app.selectbox[1].set_value("Pharmacy")
    app.button[0].click().run()
    assert not app.exception
    assert len(app.error) == 1