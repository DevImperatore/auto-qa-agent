import os
from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


def write_suggestions(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate prioritized code improvement suggestions in Markdown using Gemini."""
    if state.get("error"):
        return {"suggestions": "", "error": state["error"]}

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "suggestions": "",
            "error": "GOOGLE_API_KEY environment variable is not configured.",
        }

    analysis = state.get("analysis", "")
    if not analysis:
        return {
            "suggestions": "",
            "error": "No code analysis available to generate review suggestions.",
        }

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            google_api_key=api_key,
        )

        system_instruction = (
            "You are a senior engineering peer reviewer. Transform technical analysis into clear, "
            "actionable, and constructive code review suggestions for the pull request author. "
            "Output must be in Markdown format. "
            "STRICT RULE: Do NOT use any emojis anywhere in the text or headings."
        )

        prompt_content = (
            f"Given the following technical code analysis of a pull request:\n\n"
            f"{analysis}\n\n"
            "Generate at most 5 prioritized suggestions for improvements. Follow these requirements:\n"
            "- Exactly 1 to 5 recommendations, ordered from highest to lowest priority.\n"
            "- Use clean Markdown structure (headers, bold labels, code blocks if necessary).\n"
            "- For each suggestion provide:\n"
            "  * Priority level: High, Medium, or Low\n"
            "  * Affected file or component\n"
            "  * Explanation of the issue\n"
            "  * Concrete remediation guidance or suggested snippet\n"
            "- Maintain an objective, constructive, and professional engineering tone.\n"
            "- Zero emojis."
        )

        response = llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=prompt_content),
        ])

        suggestions_result = response.content if isinstance(response.content, str) else str(response.content)

        return {
            "suggestions": suggestions_result,
            "error": None,
        }

    except Exception as exc:
        return {
            "suggestions": "",
            "error": f"Error generating review suggestions: {str(exc)}",
        }
