import json
import shlex
import sys

import httpx
import pytest

from dash.cache import Cache
from dash.config import Config, WidgetConfig
from dash.registry import Registry
from dash.runner import run_widgets
from dash.widgets.github_tasks import GitHubError, GitHubTasksWidget

SECRET = "ghp_COMMANDOUTPUTSECRET999"


def py(code: str) -> str:
    """A token_cmd string that runs a tiny Python program (no shell involved)."""
    return shlex.join([sys.executable, "-c", code])


def widget(env=None, timeout=5.0, seen=None):
    def handler(request):
        if seen is not None:
            seen.append(request.headers["authorization"])
        return httpx.Response(200, json={"total_count": 0, "items": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return GitHubTasksWidget(client=client, env={} if env is None else env, token_cmd_timeout=timeout)


def test_token_comes_from_the_command_when_env_is_unset():
    seen = []
    widget(seen=seen).fetch({"token_cmd": py("print('tok_from_cmd')")})
    assert seen and set(seen) == {"Bearer tok_from_cmd"}


def test_environment_variable_wins_and_command_is_not_run(tmp_path):
    marker = tmp_path / "ran"
    seen = []
    widget(env={"GITHUB_TOKEN": "from_env"}, seen=seen).fetch(
        {"token_cmd": py(f"open({str(marker)!r}, 'w').write('x'); print('tok')")})
    assert set(seen) == {"Bearer from_env"} and not marker.exists()


def test_missing_token_mentions_variable_and_token_cmd():
    with pytest.raises(GitHubError) as exc:
        widget().fetch({})
    msg = str(exc.value)
    assert "GITHUB_TOKEN" in msg and "token_cmd" in msg


def test_custom_token_env_name_is_reported():
    with pytest.raises(GitHubError, match="MY_GH"):
        widget().fetch({"token_env": "MY_GH"})


def test_nonzero_exit_reports_failure_without_output():
    cmd = py(f"import sys; print('{SECRET}'); print('{SECRET}', file=sys.stderr); sys.exit(3)")
    with pytest.raises(GitHubError) as exc:
        widget().fetch({"token_cmd": cmd})
    assert "failed" in str(exc.value) and "3" in str(exc.value) and SECRET not in str(exc.value)


@pytest.mark.parametrize("code", ["print()", "print('   ')", "pass"])
def test_empty_output_reports_no_token(code):
    with pytest.raises(GitHubError, match="produced no token"):
        widget().fetch({"token_cmd": py(code)})


@pytest.mark.parametrize("code", [f"print('{SECRET} extra')", f"print('{SECRET}'); print('{SECRET}')"])
def test_more_than_one_word_is_rejected_and_not_shown(code):
    with pytest.raises(GitHubError) as exc:
        widget().fetch({"token_cmd": py(code)})
    assert "not a single token" in str(exc.value) and SECRET not in str(exc.value)


def test_undecodable_output_is_rejected():
    with pytest.raises(GitHubError, match="not a single token"):
        widget().fetch({"token_cmd": py("import sys; sys.stdout.buffer.write(b'\\xff\\xfe')")})


def test_hanging_command_is_stopped_and_reported():
    import time
    start = time.monotonic()
    with pytest.raises(GitHubError, match="timed out"):
        widget(timeout=0.5).fetch({"token_cmd": py("import time; time.sleep(30)")})
    assert time.monotonic() - start < 5


def test_missing_executable_names_it():
    with pytest.raises(GitHubError, match="could not be started: definitely-not-a-real-command"):
        widget().fetch({"token_cmd": "definitely-not-a-real-command --flag"})


@pytest.mark.parametrize("bad", ["", "   ", 5, ["gh", "auth", "token"]])
def test_invalid_token_cmd_option(bad):
    with pytest.raises(GitHubError, match="non-empty command string"):
        widget().fetch({"token_cmd": bad})


def test_unbalanced_quotes():
    with pytest.raises(GitHubError, match="could not be parsed"):
        widget().fetch({"token_cmd": "echo 'oops"})


def test_command_runs_without_a_shell(tmp_path):
    marker = tmp_path / "injected"
    # shell metacharacters are plain arguments, never interpreted
    with pytest.raises(GitHubError):
        widget().fetch({"token_cmd": f"definitely-not-a-real-command ; touch {marker}"})
    assert not marker.exists()


def test_token_from_command_never_persisted_or_output(tmp_path):
    cache = Cache(tmp_path / "cache")
    reg = Registry()
    reg.register(widget())
    cmd = py(f"print('{SECRET}')")
    results = run_widgets(Config([WidgetConfig("github", {"token_cmd": cmd, "limit": 3})], 10.0), reg, cache)
    assert results[0].status == "ok"
    blobs = [json.dumps([r.to_dict() for r in results])]
    blobs += [f.read_text() for f in (tmp_path / "cache").rglob("*") if f.is_file()]
    assert blobs and all(SECRET not in b for b in blobs)


def test_failure_through_the_runner_does_not_leak_command_output(tmp_path):
    reg = Registry()
    reg.register(widget())
    cmd = py(f"import sys; print('{SECRET}'); sys.exit(1)")
    results = run_widgets(Config([WidgetConfig("github", {"token_cmd": cmd})], 10.0), reg, Cache(tmp_path / "c"))
    assert results[0].status == "error" and SECRET not in json.dumps(results[0].to_dict())
