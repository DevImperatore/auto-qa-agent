from typing import TypedDict, Optional


class PRReviewState(TypedDict):
    pr_number: int
    repo_name: str
    diff: str
    file_count: int
    analysis: str
    suggestions: str
    comment_posted: bool
    error: Optional[str]
