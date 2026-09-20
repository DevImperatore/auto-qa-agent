import os
from typing import Any, Dict
from github import Github, Auth
from github.GithubException import GithubException


def post_comment(state: Dict[str, Any]) -> Dict[str, Any]:
    """Post generated suggestions as a review comment on the pull request via PyGitHub."""
    if state.get("error"):
        return {"comment_posted": False, "error": state["error"]}

    token = os.getenv("GITHUB_TOKEN")
    repo_name = state.get("repo_name")
    pr_number = state.get("pr_number")
    suggestions = state.get("suggestions", "")

    if not token:
        return {
            "comment_posted": False,
            "error": "GITHUB_TOKEN environment variable is not configured.",
        }

    if not repo_name or not pr_number:
        return {
            "comment_posted": False,
            "error": f"Invalid PR details: repo_name={repo_name}, pr_number={pr_number}.",
        }

    if not suggestions or not suggestions.strip():
        return {
            "comment_posted": False,
            "error": "No suggestions available to post to the pull request.",
        }

    comment_body = f"## Auto QA Agent Review\n\n{suggestions.strip()}\n\n---\n*Automated review posted by Auto QA Agent.*"

    try:
        auth = Auth.Token(token)
        gh = Github(auth=auth)
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))

        pr.create_issue_comment(comment_body)

        return {
            "comment_posted": True,
            "error": None,
        }

    except GithubException as exc:
        msg = exc.data.get("message", str(exc)) if isinstance(exc.data, dict) else str(exc)
        return {
            "comment_posted": False,
            "error": f"GitHub API error ({exc.status}) posting comment: {msg}",
        }
    except Exception as exc:
        return {
            "comment_posted": False,
            "error": f"Unexpected error posting comment: {str(exc)}",
        }
