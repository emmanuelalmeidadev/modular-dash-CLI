"""GitHub tasks widget: issues assigned to me and PRs awaiting my review."""
from __future__ import annotations

import os
from typing import Any, Mapping

import httpx

SEARCH_URL = "https://api.github.com/search/issues"
DEFAULT_TOKEN_ENV = "GITHUB_TOKEN"
DEFAULT_LIMIT = 5
_REPO_PREFIX = "https://api.github.com/repos/"


class GitHubError(Exception):
    pass


class GitHubTasksWidget:
    id = "github"
    title = "GitHub"
    default_ttl = 300

    def __init__(self, client: httpx.Client | None = None, env: Mapping[str, str] | None = None):
        self._client = client
        self._env = env if env is not None else os.environ

    def fetch(self, options: dict[str, Any]) -> dict[str, Any]:
        token_env = str(options.get("token_env", DEFAULT_TOKEN_ENV))
        token = self._env.get(token_env)
        if not token:
            raise GitHubError(f"set the {token_env} environment variable to a GitHub token")
        limit = options.get("limit", DEFAULT_LIMIT)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise GitHubError("option 'limit' must be a positive integer")

        client = self._client or httpx.Client(timeout=8.0)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            issues = self._search(client, headers, "is:issue is:open assignee:@me archived:false", limit)
            reviews = self._search(client, headers, "is:pr is:open review-requested:@me archived:false", limit)
        except httpx.HTTPError as exc:
            raise GitHubError(f"GitHub unavailable: {exc.__class__.__name__}") from exc
        finally:
            if self._client is None:
                client.close()
        return {"assigned_issues": issues, "review_requests": reviews}

    def _search(self, client: httpx.Client, headers: dict[str, str], query: str, limit: int) -> dict[str, Any]:
        resp = client.get(SEARCH_URL, params={"q": query, "per_page": limit, "sort": "updated"}, headers=headers)
        self._raise_for_error(resp)
        try:
            body = resp.json()
            items = [
                {
                    "repo": str(i["repository_url"]).removeprefix(_REPO_PREFIX),
                    "number": i["number"],
                    "title": i["title"],
                    "url": i["html_url"],
                }
                for i in body["items"][:limit]
            ]
            return {"total": body["total_count"], "items": items}
        except (KeyError, TypeError, ValueError):
            raise GitHubError("GitHub returned an unexpected response") from None

    @staticmethod
    def _raise_for_error(resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return
        if resp.status_code == 401:
            raise GitHubError("GitHub rejected the token (401): check that it is valid")
        rate_limited = resp.status_code == 429 or (
            resp.status_code == 403 and (resp.headers.get("x-ratelimit-remaining") == "0" or "rate limit" in resp.text.lower())
        )
        if rate_limited:
            raise GitHubError("GitHub rate limit exceeded; try again later")
        if resp.status_code == 403:
            raise GitHubError("GitHub denied the request (403): the token may lack access")
        raise GitHubError(f"GitHub returned HTTP {resp.status_code}")
