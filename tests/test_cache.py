from dash.cache import Cache
from dash.config import Config, WidgetConfig
from dash.registry import Registry
from dash.runner import run_widgets


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def setup(tmp_path, fake_widget, fetch=None, ttl=60):
    clock = Clock()
    cache = Cache(tmp_path / "c", clock=clock)
    w = fake_widget("w", fetch, ttl=ttl)
    reg = Registry()
    reg.register(w)
    return clock, cache, w, reg


def run(reg, cache, refresh=False, wc=None):
    return run_widgets(Config([wc or WidgetConfig("w")], 5.0), reg, cache, refresh=refresh)[0]


def test_hit_skips_fetch(tmp_path, fake_widget):
    clock, cache, w, reg = setup(tmp_path, fake_widget)
    run(reg, cache)
    clock.now += 30
    r = run(reg, cache)
    assert w.calls == 1 and r.status == "ok" and not r.stale


def test_expiry_refetches(tmp_path, fake_widget):
    clock, cache, w, reg = setup(tmp_path, fake_widget)
    run(reg, cache)
    clock.now += 61
    run(reg, cache)
    assert w.calls == 2


def test_refresh_bypasses_cache(tmp_path, fake_widget):
    _, cache, w, reg = setup(tmp_path, fake_widget)
    run(reg, cache)
    run(reg, cache, refresh=True)
    assert w.calls == 2


def test_stale_data_served_when_fetch_fails(tmp_path, fake_widget):
    state = {"fail": False}

    def fetch(o):
        if state["fail"]:
            raise RuntimeError("down")
        return {"v": 7}

    clock, cache, w, reg = setup(tmp_path, fake_widget, fetch)
    run(reg, cache)
    clock.now += 500
    state["fail"] = True
    r = run(reg, cache)
    assert r.status == "ok" and r.stale and r.data == {"v": 7}


def test_errors_are_not_cached(tmp_path, fake_widget):
    def fetch(o):
        raise RuntimeError("down")

    _, cache, w, reg = setup(tmp_path, fake_widget, fetch)
    assert run(reg, cache).status == "error"
    assert cache.get("w", {}) is None


def test_zero_ttl_widget_never_cached(tmp_path, fake_widget):
    _, cache, w, reg = setup(tmp_path, fake_widget, ttl=0)
    run(reg, cache)
    run(reg, cache)
    assert w.calls == 2 and cache.get("w", {}) is None


def test_ttl_override_from_config(tmp_path, fake_widget):
    clock, cache, w, reg = setup(tmp_path, fake_widget, ttl=60)
    wc = WidgetConfig("w", ttl=10)
    run(reg, cache, wc=wc)
    clock.now += 11
    run(reg, cache, wc=wc)
    assert w.calls == 2


def test_different_options_have_separate_entries(tmp_path, fake_widget):
    _, cache, w, reg = setup(tmp_path, fake_widget)
    run(reg, cache, wc=WidgetConfig("w", {"loc": "a"}))
    run(reg, cache, wc=WidgetConfig("w", {"loc": "b"}))
    assert w.calls == 2


def test_corrupt_cache_file_is_a_miss(tmp_path, fake_widget):
    _, cache, w, reg = setup(tmp_path, fake_widget)
    run(reg, cache)
    for f in (tmp_path / "c").glob("*.json"):
        f.write_text("{not json")
    assert run(reg, cache).status == "ok" and w.calls == 2
