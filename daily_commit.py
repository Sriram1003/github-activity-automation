import argparse
import random
import sys
from datetime import datetime

from utils.config_loader import load_config, get_github_token
from utils.logger import setup_logger
from utils.state_manager import StateManager
from utils.github_api import GitHubAPI

logger = setup_logger("daily_commit")

def parse_args():
    parser = argparse.ArgumentParser(description="Daily Commit Agent")
    parser.add_argument("--force", action="store_true", help="Bypass once-per-day guard")
    return parser.parse_args()

def run_agent():
    args = parse_args()
    config = load_config()
    agent_config = config.get("daily_commit", {})
    
    state_manager = StateManager()
    today = datetime.now().strftime("%Y-%m-%d")
    
    last_run_date = state_manager.get_last_run_date()
    if last_run_date == today and not args.force:
        logger.info(f"Agent already ran successfully today ({today}). Use --force to bypass. Exiting.")
        return

    token = get_github_token()
    if not token:
        logger.error("No GITHUB_TOKEN found. Exiting.")
        sys.exit(1)

    api = GitHubAPI(token)
    
    try:
        user_info = api.get_authenticated_user()
        username = user_info.get("login")
        logger.info(f"Authenticated as {username}")
        
        repos = api.get_eligible_repositories(username)
        if not repos:
            logger.error("No eligible repositories found for this user.")
            sys.exit(1)
            
        last_repo = state_manager.get_last_repo()
        
        # Filter out the last used repo if we have more than one choice
        available_repos = [r for r in repos if r["name"] != last_repo]
        if not available_repos:
            available_repos = repos # Fallback if they only have one repo
            
        selected_repo = random.choice(available_repos)
        repo_name = selected_repo["name"]
        logger.info(f"Selected repository: {repo_name}")
        
        target_file = agent_config.get("target_file", ".contributions")
        commit_range = agent_config.get("commit_count_range", {"min": 1, "max": 3})
        commit_count = random.randint(commit_range.get("min", 1), commit_range.get("max", 3))
        messages = agent_config.get("commit_messages", ["Update"])
        
        for i in range(commit_count):
            file_info = api.get_file_info(username, repo_name, target_file)
            sha = file_info["sha"] if file_info else None
            
            commit_message = random.choice(messages)
            content = f"Activity update: {datetime.now().isoformat()}\n"
            
            api.create_or_update_file(
                owner=username,
                repo=repo_name,
                file_path=target_file,
                message=commit_message,
                content=content,
                sha=sha
            )
            logger.info(f"Commit {i+1}/{commit_count} to {repo_name}/{target_file} successful.")
            
        # Record success
        state_manager.update_daily_commit(today, repo_name)
        logger.info("Daily Commit Agent completed successfully.")
        
    except Exception as e:
        logger.error(f"Daily Commit Agent failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_agent()
