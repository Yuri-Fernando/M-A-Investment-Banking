from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "src" / "ma_deallab" / "ui" / "app.py"


@pytest.fixture(scope="module", autouse=True)
def initialized_chart_runtime():
    """Initialize Plotly schemas before the interaction timeout starts."""
    import plotly.express as px

    px.bar(x=["warmup"], y=[0])


def test_dashboard_all_sections_and_scenarios():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    for scenario in ("downside", "upside", "base"):
        at.sidebar.selectbox[0].select(scenario).run()
        assert not at.exception
    for page in at.sidebar.radio[0].options:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, page


def test_dashboard_invalid_terminal_growth_blocks():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    at.sidebar.checkbox[0].check()
    at.sidebar.number_input[3].set_value(30.0).run()
    assert not at.exception
    assert any("WACC" in e.value for e in at.error)


def test_editable_drivers_follow_selected_scenario():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    at.sidebar.selectbox[0].select("downside").run()
    assert at.sidebar.number_input[0].value == 5.0
    assert at.sidebar.number_input[1].value == 17.0
    at.sidebar.selectbox[0].select("upside").run()
    assert at.sidebar.number_input[0].value == 18.0
    assert at.sidebar.number_input[1].value == 25.0
