# Auto QA Agent

Automated multi-agent Pull Request review system built with Python, LangGraph, and Google Gemini.

The system integrates directly with GitHub pull requests, extracts the unified diff, analyzes code complexity, architectural patterns, and type annotations, generates actionable recommendations, and posts feedback comments directly on the pull request thread.

---

## Architecture Flow

The workflow is modeled as a compiled state graph (`StateGraph`) using LangGraph with conditional error routing.

```
       +-----------------------+
       |         START         |
       +-----------------------+
                   |
                   v
       +-----------------------+
       |       pr_fetcher      |
       |  (Extract PR Diff)    |
       +-----------------------+
                   |
          [ Error Detected? ]
              /        \
       (Yes) /          \ (No)
            v            v
       +---------+  +-----------------------+
       |   END   |  |     code_analyzer     |
       +---------+  | (Gemini 1.5 Flash LLM)|
                    +-----------------------+
                                 |
                                 v
                    +-----------------------+
                    |   suggestion_writer   |
                    | (Markdown Synthesizer)|
                    +-----------------------+
                                 |
                                 v
                    +-----------------------+
                    |      pr_commenter     |
                    | (GitHub Issue Comment)|
                    +-----------------------+
                                 |
                                 v
                            +---------+
                            |   END   |
                            +---------+
```

---

## Core Components and Node Execution

1. **State Definition (`agent/state.py`):**
   Maintains a centralized `PRReviewState` schema across all lifecycle stages:
   - `pr_number` (int): GitHub Pull Request identifier.
   - `repo_name` (str): Repository slug in `owner/repository` format.
   - `diff` (str): Unified diff across all modified files.
   - `file_count` (int): Number of changed files.
   - `analysis` (str): Structural analysis output from the LLM.
   - `suggestions` (str): Formatted Markdown recommendations.
   - `comment_posted` (bool): Execution status indicator.
   - `error` (Optional[str]): Failure diagnostic message if any step encounters an exception.

2. **PR Fetcher Node (`agent/nodes/pr_fetcher.py`):**
   - Connects to the GitHub REST API via PyGitHub using authenticated tokens.
   - Inspects pull request file patches, calculates changed file counts, and stitches together the unified diff.
   - Gracefully handles missing tokens, API rate limits, or network exceptions by recording details into `state['error']`.

3. **Code Analyzer Node (`agent/nodes/code_analyzer.py`):**
   - Transmits diff content to Google Gemini (`gemini-1.5-flash`) via `langchain-google-genai`.
   - Inspects cyclomatic complexity, nested branch depth, methods exceeding 50 lines, typing coverage, and error boundary gaps.
   - Implements diff payload boundary guarding to avoid token window overflows on massive revisions.

4. **Suggestion Writer Node (`agent/nodes/suggestion_writer.py`):**
   - Converts the technical analysis into a prioritized list of up to 5 concrete recommendations.
   - Assigns priority severity levels (High, Medium, Low) with concrete remediation advice and code snippets.
   - Enforces a professional, constructive engineering tone without informal clutter.

5. **PR Commenter Node (`agent/nodes/pr_commenter.py`):**
   - Posts the final review document to the pull request thread using PyGitHub (`create_issue_comment`).
   - Appends standardized header markers (`## Auto QA Agent Review`) and automated signatures.
   - Flags `comment_posted = True` upon successful submission.

6. **Graph Orchestration (`agent/graph.py`):**
   - Compiles the nodes into a `StateGraph`.
   - Applies conditional edge routing `should_continue` following diff retrieval to halt early on GitHub API or permission failures.

---

## Tech Stack

- **Runtime:** Python 3.12+
- **Agent Framework:** LangGraph (StateGraph multi-agent flow)
- **Large Language Model:** Google Gemini (`gemini-1.5-flash`) via `langchain-google-genai`
- **GitHub Integration:** PyGitHub 2.4+
- **Configuration:** Python-dotenv
- **CI/CD:** GitHub Actions

---

## Setup and Configuration

### Prerequisites

- Python 3.12 or higher.
- A GitHub Personal Access Token (PAT) with `repo` or `pull-requests: write` permissions (or repository default GitHub Actions token).
- A Google Gemini API Key from Google AI Studio.

### Local Installation

1. Clone repository and navigate to the project directory:
   ```bash
   cd auto-qa-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your real keys:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key
   GITHUB_TOKEN=your_github_personal_access_token
   GITHUB_REPO=owner/repository-name
   ```

5. Run manually against a pull request:
   ```bash
   python agent/graph.py <PR_NUMBER>
   ```

---

## GitHub Actions Automated Deployment

A ready-to-run GitHub Actions workflow is provided in `.github/workflows/qa_agent.yml`.

### Repository Secret Configuration

Configure the following repository secret in GitHub under **Settings > Secrets and variables > Actions**:

| Secret Name | Description |
|---|---|
| `GOOGLE_API_KEY` | Gemini API key from Google AI Studio |

The workflow automatically provides `GITHUB_TOKEN` from the runner context and requires write permissions for pull requests:

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

Whenever a pull request is opened or updated (`types: [opened, synchronize]`), the agent executes the graph and posts review feedback directly into the discussion thread.

---

## Known Limitations

- **Binary Files:** Binary files and non-patch assets (e.g. images, compiled binaries) are detected but cannot be statically reviewed by the LLM.
- **Diff Truncation:** Diffs exceeding 80,000 characters are safely truncated to fit within optimal context constraints, which may omit lower-order files in very large PRs.
- **Token Rate Limits:** GitHub API calls are subject to repository or personal token rate limits (standard 5,000 requests/hour for authenticated calls).
- **Line-level Annotations:** Current implementation posts a consolidated pull request summary comment rather than line-level GitHub review thread discussions.
