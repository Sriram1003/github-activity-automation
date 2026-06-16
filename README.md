# GitHub Activity Automation System

A robust, configurable, automated tool to maintain repository activity and auto-generate mini-projects on a schedule using the GitHub REST API v3. 

## Project Overview

This system comprises two automated agents:
1. **Daily Commit Agent:** Periodically makes configurable commits to a random repository to maintain a healthy GitHub contribution graph.
2. **Project Creator Agent:** Generates unique open-source project ideas (via HuggingFace API or built-in fallbacks) and pushes brand-new stub projects to your GitHub account on a regular schedule.

## Prerequisites

- **Python:** 3.10+
- **Git:** Installed and available in PATH.
- **OS:** Cross-platform (Windows, Linux, macOS).

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd "GitHub Activity Automation System"
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Environment Variables:**
   Copy the example environment file and fill in your details:
   ```bash
   cp .env.example .env
   ```

## Configuration Guide

The system uses `config.yaml` for all configurable parameters.

### Global Configuration
- `kill_switch` (`false`|`true`): When set to `true`, halts both agents immediately without making any API calls.

### Daily Commit Agent
- `daily_commit.target_file`: The filename to commit to (default: `.contributions`).
- `daily_commit.commit_count_range`: Min and max number of commits per run.
- `daily_commit.commit_messages`: A list of potential commit messages to randomly select from.

### Project Creator Agent
- `project_creator.frequency_days`: How often (in days) the agent should create a new repository.
- `project_creator.supported_languages`: A list of languages (e.g., `python`, `javascript`) to scaffold. Ensure corresponding directories exist in the `templates/` folder.
- `project_creator.external_api`: Configuration for the HuggingFace API integration.
- `project_creator.fallback_ideas`: Built-in ideas to use if the external AI API fails or is unavailable.

## API Key Setup

### GitHub Personal Access Token (PAT)
1. Go to your GitHub Settings -> Developer settings -> Personal access tokens -> Tokens (classic).
2. Generate a new token with the `repo` scope (full control of private repositories).
3. Copy the token and paste it into the `.env` file:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

### HuggingFace Token (Optional)
1. Sign up/Log in to [HuggingFace](https://huggingface.co/).
2. Go to Settings -> Access Tokens and generate a new token (read role is sufficient).
3. Add it to your `.env` file:
   ```
   HUGGINGFACE_API_TOKEN=hf_your_token_here
   ```

## Running the Agents

Both agents can be run manually from the command line.

### Daily Commit Agent
Runs normally (will exit if already run today):
```bash
python daily_commit.py
```
Force the agent to run, ignoring the once-per-day guard:
```bash
python daily_commit.py --force
```

### Project Creator Agent
Runs normally (will exit if the configured frequency hasn't passed):
```bash
python project_creator.py
```
Force the agent to create a project immediately:
```bash
python project_creator.py --force
```

## Scheduling

You can automate the execution of these agents using your OS's built-in scheduler.

### Linux/macOS (Cron)
Run `crontab -e` and add the following lines to run the agents daily at noon:
```cron
0 12 * * * cd /path/to/project && /path/to/project/venv/bin/python daily_commit.py
0 12 * * * cd /path/to/project && /path/to/project/venv/bin/python project_creator.py
```

### Windows (Task Scheduler)
1. Open Task Scheduler and create a "Basic Task".
2. Set the trigger to "Daily".
3. For the Action, select "Start a program".
4. Program/script: `C:\path\to\project\venv\Scripts\python.exe`
5. Add arguments: `daily_commit.py`
6. Start in: `C:\path\to\project`
7. Repeat the process for `project_creator.py`.

## Kill Switch
To pause or stop the agents permanently without removing cron jobs, edit `config.yaml` and set:
```yaml
kill_switch: true
```

## Troubleshooting

1. **Error: `GITHUB_TOKEN is missing`**
   - **Fix:** Ensure you have created a `.env` file in the root directory and assigned your PAT to `GITHUB_TOKEN`.
2. **Error: `GitHub API rate limit running low` or `HTTP 403 Forbidden` (rate limit exceeded)**
   - **Fix:** GitHub restricts API calls to 5000/hr for authenticated users. Wait an hour or check if another application is consuming your rate limits. The agent will log the error and exit gracefully.
3. **Error: `External AI API failed`**
   - **Fix:** This usually means the HuggingFace token is invalid, missing, or the model is loading. The system will automatically degrade gracefully to the built-in fallback list, so no further action is strictly necessary unless you insist on AI-generated ideas.

## Project Structure

```
.
├── config.yaml          # All configurable settings
├── daily_commit.py      # Entry point for the Daily Commit Agent
├── project_creator.py   # Entry point for the Project Creator Agent
├── README.md            # Comprehensive documentation
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment variables
├── state.json           # (Generated) Local persistence of agent state
├── templates/           # Starter files for new projects
│   ├── python/          # Python scaffold
│   └── javascript/      # JavaScript scaffold
├── tests/               # Unit and integration tests
│   └── test_agents.py   # Tests for idempotency and random repo selection
└── utils/               # Core modules and helper utilities
    ├── ai_client.py     # Wrapper for the HuggingFace Inference API
    ├── config_loader.py # Configuration and secrets loading
    ├── github_api.py    # Robust wrapper for GitHub REST API v3
    ├── logger.py        # Structured logging setup
    └── state_manager.py # JSON-based state persistence
```
