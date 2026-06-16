import json
import os
from utils.logger import setup_logger

logger = setup_logger("state_manager")

class StateManager:
    def __init__(self, state_file: str = "state.json"):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if not os.path.exists(self.state_file):
            return {
                "daily_commit_last_run_date": None,
                "daily_commit_last_repo": None,
                "created_projects": []
            }
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read state file: {e}. Starting fresh.")
            return {
                "daily_commit_last_run_date": None,
                "daily_commit_last_repo": None,
                "created_projects": []
            }

    def save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save state file: {e}")

    def update_daily_commit(self, run_date: str, repo_name: str):
        self.state["daily_commit_last_run_date"] = run_date
        self.state["daily_commit_last_repo"] = repo_name
        self.save_state()

    def add_created_project(self, name: str, date: str, language: str):
        if "created_projects" not in self.state:
            self.state["created_projects"] = []
        self.state["created_projects"].append({
            "name": name,
            "date": date,
            "language": language
        })
        self.save_state()

    def get_last_run_date(self) -> str:
        return self.state.get("daily_commit_last_run_date")

    def get_last_repo(self) -> str:
        return self.state.get("daily_commit_last_repo")

    def get_created_projects(self) -> list:
        return self.state.get("created_projects", [])
