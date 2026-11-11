import time

import pytest

from dash.config import Config, WidgetConfig
from dash.registry import Registry
from dash.runner import run_widgets


def make(registry_widgets, wcs, timeout=5.0):
    reg = Registry()
    for w in registry_widgets:
        reg.register(w)
    return Config(widgets=wcs, timeout=timeout), reg


def boom(_):
    raise RuntimeError("network down")


def test_results_keep_config_order(fake_widget, cache):
    cfg, reg = make([fake_widget("a"), fake_widget("b")], [WidgetConfig("b"), WidgetConfig("a")])
    assert [r.id for r in run_widgets(cfg, reg, cache)] == ["b", "a"]


def test_unknown_widget_is_error_and_others_run(fake_widget, cache):
    cfg, reg = make([fake_widget("a")], [WidgetConfig("ghost"), WidgetConfig("a")])
    results = run_widgets(cfg, reg, cache)
    assert results[0].status == "error" and "ghost" in results[0].error
    assert results[1].status == "ok"


def test_raising_widget_is_isolated(fake_widget, cache):
    cfg, reg = make([fake_widget("bad", boom), fake_widget("good")], [WidgetConfig("bad"), WidgetConfig("good")])
    bad, good = run_widgets(cfg, reg, cache)
    assert bad.status == "error" and "network down" in bad.error
    assert good.status == "ok"


def test_hanging_widget_times_out(fake_widget, cache):
    cfg, reg = make(
        [fake_widget("slow", lambda o: time.sleep(5) or {}), fake_widget("good")],
        [WidgetConfig("slow"), WidgetConfig("good")],
        timeout=0.3,
    )
    start = time.monotonic()
    slow, good = run_widgets(cfg, reg, cache)
    assert time.monotonic() - start < 2
    assert slow.status == "error" and "timed out" in slow.error
    assert good.status == "ok"


def test_two_slow_widgets_run_concurrently(fake_widget, cache):
    sleeper = lambda o: time.sleep(2) or {"x": 1}
    cfg, reg = make([fake_widget("a", sleeper), fake_widget("b", sleeper)], [WidgetConfig("a"), WidgetConfig("b")], timeout=10)
    start = time.monotonic()
    results = run_widgets(cfg, reg, cache)
    assert time.monotonic() - start < 4
    assert all(r.status == "ok" for r in results)
