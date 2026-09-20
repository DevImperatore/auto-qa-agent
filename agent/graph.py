import os
import sys
from typing import Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from agent.state import PRReviewState
from agent.nodes.pr_fetcher import fetch_pr
from agent.nodes.code_analyzer import analyze_code
from agent.nodes.suggestion_writer import write_suggestions
from agent.nodes.pr_commenter import post_comment


def should_continue(state: PRReviewState) -> str:
    """Conditional router determining whether to proceed with analysis or terminate on error."""
    return END if state.get("error") else "analyze"


def build_graph() -> Any:
    """Construct and compile the LangGraph workflow for pull request review."""
    graph = StateGraph(PRReviewState)

    graph.add_node("fetch", fetch_pr)
    graph.add_node("analyze", analyze_code)
    graph.add_node("suggest", write_suggestions)
    graph.add_node("comment", post_comment)

    graph.set_entry_point("fetch")
    graph.add_conditional_edges("fetch", should_continue, {"analyze": "analyze", END: END})
    graph.add_edge("analyze", "suggest")
    graph.add_edge("suggest", "comment")
    graph.add_edge("comment", END)

    return graph.compile()


if __name__ == "__main__":
    load_dotenv()

    pr_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    repo_name = os.getenv("GITHUB_REPO", "owner/repo")

    app = build_graph()
    result = app.invoke({
        "pr_number": pr_number,
        "repo_name": repo_name,
        "diff": "",
        "file_count": 0,
        "analysis": "",
        "suggestions": "",
        "comment_posted": False,
        "error": None,
    })

    print("Done:", result.get("comment_posted"), "| Error:", result.get("error"))
