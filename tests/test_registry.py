import pytest

from dash.registry import Registry


def test_register_and_lookup(fake_widget):
    reg = Registry()
    w = fake_widget("weather")
    reg.register(w)
    assert reg.get("weather") is w
    assert reg.ids() == ["weather"]


def test_unknown_id_returns_none():
    assert Registry().get("nope") is None


def test_duplicate_registration_rejected(fake_widget):
    reg = Registry()
    reg.register(fake_widget("a"))
    with pytest.raises(ValueError):
        reg.register(fake_widget("a"))
