import os
from typing import Any, Dict
from github import Github, Auth
from github.GithubException import GithubException


def fetch_pr(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch PR details, changed files, and unified diff using PyGitHub."""
    token = os.getenv("GITHUB_TOKEN")
    repo_name = state.get("repo_name")
    pr_number = state.get("pr_number")

    if not token:
        return {
            "diff": "",
            "file_count": 0,
            "error": "GITHUB_TOKEN environment variable is not configured.",
        }

    if not repo_name or not pr_number:
        return {
            "diff": "",
            "file_count": 0,
            "error": f"Invalid repository parameters: repo_name={repo_name}, pr_number={pr_number}.",
        }

    try:
        auth = Auth.Token(token)
        gh = Github(auth=auth)
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))

        changed_files = list(pr.get_files())
        file_count = len(changed_files)

        diff_chunks = []
        for file_item in changed_files:
            file_header = (
                f"diff --git a/{file_item.filename} b/{file_item.filename}\n"
                f"status: {file_item.status}, +{file_item.additions} -{file_item.deletions}"
            )
            diff_chunks.append(file_header)

            if file_item.patch:
                diff_chunks.append(file_item.patch)
            else:
                diff_chunks.append("[Binary file or no diff patch generated]")

            diff_chunks.append("-" * 40)

        full_diff = "\n".join(diff_chunks)
        if not full_diff.strip():
            full_diff = "No file modifications found in this pull request."

        return {
            "diff": full_diff,
            "file_count": file_count,
            "error": None,
        }

    except GithubException as exc:
        msg = exc.data.get("message", str(exc)) if isinstance(exc.data, dict) else str(exc)
        return {
            "diff": "",
            "file_count": 0,
            "error": f"GitHub API error ({exc.status}): {msg}",
        }
    except Exception as exc:
        return {
            "diff": "",
            "file_count": 0,
            "error": f"Unexpected error while fetching PR diff: {str(exc)}",
        }
