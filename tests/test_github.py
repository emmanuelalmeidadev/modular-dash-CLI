import json

import httpx
import pytest

from dash.config import Config, WidgetConfig
from dash.registry import Registry
from dash.result import WidgetResult
from dash.runner import run_widgets
from dash.widgets.github_tasks import GitHubError, GitHubTasksWidget

TOKEN = "ghp_SUPERSECRETTOKENVALUE123"


def item(n, repo="octo/repo"):
    return {
        "repository_url": f"https://api.github.com/repos/{repo}",
        "number": n, "title": f"Thing {n}", "html_url": f"https://github.com/{repo}/issues/{n}",
    }


def make(handler, env=None):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return GitHubTasksWidget(client=client, env={"GITHUB_TOKEN": TOKEN} if env is None else env)


def search_handler(issue_total=8, review_total=1):
    def handler(request):
        q = request.url.params["q"]
        per = int(request.url.params["per_page"])
        if "assignee" in q:
            return httpx.Response(200, json={"total_count": issue_total, "items": [item(i) for i in range(issue_total)][:per]})
        return httpx.Response(200, json={"total_count": review_total, "items": [item(100 + i) for i in range(review_total)][:per]})
    return handler


def test_items_limited_with_total_reported():
    data = make(search_handler()).fetch({"limit": 5})
    assert len(data["assigned_issues"]["items"]) == 5
    assert data["assigned_issues"]["total"] == 8
    assert data["review_requests"]["total"] == 1
    first = data["assigned_issues"]["items"][0]
    assert first == {"repo": "octo/repo", "number": 0, "title": "Thing 0", "url": "https://github.com/octo/repo/issues/0"}


def test_default_limit_is_five():
    assert len(make(search_handler(issue_total=9)).fetch({})["assigned_issues"]["items"]) == 5


def test_nothing_pending():
    data = make(search_handler(0, 0)).fetch({})
    assert data == {"assigned_issues": {"total": 0, "items": []}, "review_requests": {"total": 0, "items": []}}


def test_queries_target_authenticated_user():
    queries = []

    def handler(request):
        queries.append(request.url.params["q"])
        return httpx.Response(200, json={"total_count": 0, "items": []})

    make(handler).fetch({})
    assert any("assignee:@me" in q for q in queries) and any("review-requested:@me" in q for q in queries)


def test_missing_token_names_variable():
    with pytest.raises(GitHubError, match="GITHUB_TOKEN"):
        make(search_handler(), env={}).fetch({})


def test_custom_token_env():
    w = make(search_handler(), env={"MY_GH": "x"})
    assert w.fetch({"token_env": "MY_GH"})["review_requests"]["total"] == 1


def test_token_sent_as_bearer_header():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"total_count": 0, "items": []})

    make(handler).fetch({})
    assert seen["auth"] == f"Bearer {TOKEN}"


@pytest.mark.parametrize("response, fragment", [
    (httpx.Response(403, headers={"x-ratelimit-remaining": "0"}, text="API rate limit exceeded"), "rate limit"),
    (httpx.Response(429), "rate limit"),
    (httpx.Response(401), "token"),
    (httpx.Response(500), "HTTP 500"),
])
def test_api_errors_reported(response, fragment):
    with pytest.raises(GitHubError, match=fragment):
        make(lambda r: response).fetch({})


def test_network_failure():
    def handler(request):
        raise httpx.ConnectError("boom")

    with pytest.raises(GitHubError, match="unavailable"):
        make(handler).fetch({})


def test_invalid_limit():
    with pytest.raises(GitHubError, match="limit"):
        make(search_handler()).fetch({"limit": 0})


def test_token_never_persisted_or_output(tmp_path):
    from dash.cache import Cache

    cache = Cache(tmp_path / "cache")
    reg = Registry()
    reg.register(make(search_handler()))
    results = run_widgets(Config([WidgetConfig("github", {"limit": 3})], 5.0), reg, cache)
    assert results[0].status == "ok"
    blobs = [json.dumps([r.to_dict() for r in results])]
    blobs += [f.read_text() for f in (tmp_path / "cache").rglob("*") if f.is_file()]
    assert blobs and all(TOKEN not in b for b in blobs)


def test_token_not_in_error_message():
    with pytest.raises(GitHubError) as exc:
        make(lambda r: httpx.Response(401)).fetch({})
    assert TOKEN not in str(exc.value)
