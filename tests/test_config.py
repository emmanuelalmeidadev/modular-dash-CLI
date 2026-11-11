import pytest

from dash.config import ConfigError, load_config


def write(tmp_path, text):
    p = tmp_path / "config.toml"
    p.write_text(text)
    return p


def test_widgets_loaded_in_listed_order(tmp_path):
    cfg = load_config(write(tmp_path, """
timeout = 5
[[widgets]]
id = "weather"
ttl = 1800
[widgets.options]
location = "Lisbon"
[[widgets]]
id = "habits"
"""))
    assert [w.id for w in cfg.widgets] == ["weather", "habits"]
    assert cfg.widgets[0].options == {"location": "Lisbon"}
    assert cfg.widgets[0].ttl == 1800
    assert cfg.widgets[1].ttl is None
    assert cfg.timeout == 5.0


def test_empty_config_means_no_widgets(tmp_path):
    assert load_config(write(tmp_path, "")).widgets == []


def test_missing_file_names_expected_path(tmp_path):
    missing = tmp_path / "nope.toml"
    with pytest.raises(ConfigError) as exc:
        load_config(missing)
    assert str(missing) in str(exc.value)


def test_invalid_toml_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="invalid config"):
        load_config(write(tmp_path, "[[widgets"))


@pytest.mark.parametrize("body, fragment", [
    ('[[widgets]]\nttl = 5\n', "needs a string 'id'"),
    ('[[widgets]]\nid = "a"\nttl = -1\n', "ttl"),
    ('[[widgets]]\nid = "a"\noptions = 3\n', "options"),
    ('timeout = 0\n', "timeout"),
])
def test_invalid_shapes_rejected(tmp_path, body, fragment):
    with pytest.raises(ConfigError, match=fragment):
        load_config(write(tmp_path, body))
