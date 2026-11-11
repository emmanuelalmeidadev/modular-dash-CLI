import io
import json

from dash.cache import Cache
from dash.cli import main
from dash.registry import Registry


def run(tmp_path, fake_widget, config_text, argv=(), widgets=()):
    cfg = tmp_path / "config.toml"
    if config_text is not None:
        cfg.write_text(config_text)
    reg = Registry()
    for w in widgets:
        reg.register(w)
    out, err = io.StringIO(), io.StringIO()
    code = main(["--config", str(cfg), *argv], registry=reg, cache=Cache(tmp_path / "c"), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def test_default_run_renders_in_config_order_and_exits_zero(tmp_path, fake_widget, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    code, out, _ = run(tmp_path, fake_widget, '[[widgets]]\nid = "b"\n[[widgets]]\nid = "a"\n',
                       widgets=[fake_widget("a"), fake_widget("b")])
    assert code == 0 and out.index("B") < out.index("A")


def test_json_flag_prints_only_json(tmp_path, fake_widget):
    code, out, err = run(tmp_path, fake_widget, '[[widgets]]\nid = "a"\n', ["--json"], [fake_widget("a")])
    doc = json.loads(out)
    assert code == 0 and err == "" and [w["id"] for w in doc["widgets"]] == ["a"]


def test_partial_failure_still_exits_zero_in_both_modes(tmp_path, fake_widget, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")

    def boom(o):
        raise RuntimeError("kaput")

    widgets = [fake_widget("bad", boom), fake_widget("good")]
    cfg = '[[widgets]]\nid = "bad"\n[[widgets]]\nid = "good"\n'
    code, out, _ = run(tmp_path, fake_widget, cfg, ["--json"], widgets)
    doc = json.loads(out)
    assert code == 0 and [w["status"] for w in doc["widgets"]] == ["error", "ok"]
    code, out, _ = run(tmp_path, fake_widget, cfg, [], [fake_widget("bad", boom), fake_widget("good")])
    assert code == 0 and "kaput" in out


def test_invalid_config_exits_nonzero_with_message(tmp_path, fake_widget):
    code, out, err = run(tmp_path, fake_widget, "[[widgets", [])
    assert code != 0 and out == "" and "invalid config" in err


def test_missing_config_names_expected_path(tmp_path, fake_widget):
    code, out, err = run(tmp_path, fake_widget, None, [])
    assert code != 0 and "config.toml" in err


def test_refresh_flag_bypasses_cache(tmp_path, fake_widget):
    w = fake_widget("a")
    cfg = '[[widgets]]\nid = "a"\n'
    run(tmp_path, fake_widget, cfg, ["--json"], [w])
    run(tmp_path, fake_widget, cfg, ["--json"], [w])
    assert w.calls == 1
    run(tmp_path, fake_widget, cfg, ["--json", "--refresh"], [w])
    assert w.calls == 2
