import os
from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


def analyze_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze pull request diff for complexity, patterns, and code quality using Gemini."""
    if state.get("error"):
        return {"analysis": "", "error": state["error"]}

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "analysis": "",
            "error": "GOOGLE_API_KEY environment variable is not configured.",
        }

    diff = state.get("diff", "")
    file_count = state.get("file_count", 0)

    if not diff or diff.strip() == "No file modifications found in this pull request.":
        return {
            "analysis": "No significant code changes detected for analysis.",
            "error": None,
        }

    # Truncate extremely large diffs to avoid context overflow
    max_chars = 80000
    effective_diff = diff[:max_chars] + "\n\n[Diff truncated due to size limits]" if len(diff) > max_chars else diff

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.2,
            google_api_key=api_key,
        )

        system_instruction = (
            "You are an automated code quality engineer performing static review of a GitHub Pull Request diff. "
            "Evaluate architectural integrity, complexity, typing, and safety. "
            "Output must be strictly analytical, rigorous, and technical. "
            "Never use any emojis or informal colloquialisms."
        )

        prompt_content = (
            f"Analyze the following PR diff ({file_count} changed files):\n\n"
            f"```diff\n{effective_diff}\n```\n\n"
            "Produce a structured analysis covering:\n"
            "1. Scope of Changes: Quantity of files, additions, deletions, and newly introduced functions/classes.\n"
            "2. Cyclomatic Complexity Assessment: Identify deeply nested conditionals, loops, or complex branching paths.\n"
            "3. Function Length & Decomposition: Highlight any functions or methods exceeding approximately 50 lines.\n"
            "4. Type Safety & Annotations: Flag missing type hints, untyped parameters, and untyped return values.\n"
            "5. Error Handling & Edge Cases: Identify unhandled exceptions, missing fallback logic, or risky assertions.\n"
            "6. Anti-Patterns & Code Smells: Identify dead code, memory/resource leaks, race conditions, or performance concerns.\n\n"
            "Present your analysis clearly structured by sections without using any emojis."
        )

        response = llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=prompt_content),
        ])

        analysis_result = response.content if isinstance(response.content, str) else str(response.content)

        return {
            "analysis": analysis_result,
            "error": None,
        }

    except Exception as exc:
        return {
            "analysis": "",
            "error": f"Error during code analysis: {str(exc)}",
        }
