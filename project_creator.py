import argparse
import os
import random
import sys
from datetime import datetime

from utils.config_loader import load_config, get_github_token, get_hf_token
from utils.logger import setup_logger
from utils.state_manager import StateManager
from utils.github_api import GitHubAPI
from utils.ai_client import ProjectIdeaGenerator

logger = setup_logger("project_creator")

def parse_args():
    parser = argparse.ArgumentParser(description="Project Creator Agent")
    parser.add_argument("--force", action="store_true", help="Bypass frequency check")
    return parser.parse_args()

def load_template_files(language: str) -> dict:
    """Loads template files for a given language."""
    base_dir = os.path.join(os.path.dirname(__file__), "templates", language)
    files = {}
    if not os.path.exists(base_dir):
        logger.warning(f"No templates found for {language}")
        return files
        
    for filename in os.listdir(base_dir):
        file_path = os.path.join(base_dir, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                files[filename] = f.read()
    return files

def run_agent():
    args = parse_args()
    config = load_config()
    agent_config = config.get("project_creator", {})
    
    state_manager = StateManager()
    today_date = datetime.now()
    
    # Check frequency
    created_projects = state_manager.get_created_projects()
    if created_projects and not args.force:
        last_project = created_projects[-1]
        last_date_str = last_project.get("date")
        if last_date_str:
            last_date = datetime.fromisoformat(last_date_str)
            days_passed = (today_date - last_date).days
            frequency = agent_config.get("frequency_days", 7)
            if days_passed < frequency:
                logger.info(f"Only {days_passed} days passed since last project. Next project in {frequency - days_passed} days. Exiting.")
                return

    token = get_github_token()
    if not token:
        logger.error("No GITHUB_TOKEN found. Exiting.")
        sys.exit(1)

    api = GitHubAPI(token)
    hf_token = get_hf_token()
    
    ai_config = agent_config.get("external_api", {})
    fallback_ideas = agent_config.get("fallback_ideas", ["A generic test project."])
    
    idea_generator = ProjectIdeaGenerator(
        fallback_ideas=fallback_ideas,
        hf_token=hf_token,
        model=ai_config.get("model", "mistralai/Mistral-7B-Instruct-v0.2"),
        timeout=ai_config.get("timeout_seconds", 10)
    )
    
    try:
        user_info = api.get_authenticated_user()
        username = user_info.get("login")
        logger.info(f"Authenticated as {username}")
        
        slug, description = idea_generator.generate_project_idea()
        
        # Check for duplicates in state
        existing_names = [p["name"] for p in created_projects]
        if slug in existing_names:
            slug = f"{slug}-{random.randint(1000, 9999)}"
            
        logger.info(f"Creating repository: {slug}")
        
        # Create repository
        api.create_repository(name=slug, description=description, private=False)
        logger.info(f"Repository {slug} created successfully.")
        
        # Select language and load templates
        supported_languages = agent_config.get("supported_languages", ["python"])
        language = random.choice(supported_languages)
        logger.info(f"Selected language: {language}")
        
        files_to_commit = load_template_files(language)
        
        # Always add a README
        readme_content = f"# {slug}\n\n{description}\n\nCreated automatically by Project Creator Agent."
        files_to_commit["README.md"] = readme_content
        
        # Ensure a .gitignore is present if not in template
        if ".gitignore" not in files_to_commit:
            files_to_commit[".gitignore"] = "# Ignore file\n"
            
        # Commit files
        for filename, content in files_to_commit.items():
            api.create_or_update_file(
                owner=username,
                repo=slug,
                file_path=filename,
                message=f"Initial commit: {filename}",
                content=content
            )
            logger.info(f"Committed {filename} to {slug}")
            
        # Record success
        state_manager.add_created_project(
            name=slug, 
            date=today_date.isoformat(), 
            language=language
        )
        logger.info("Project Creator Agent completed successfully.")
        
    except Exception as e:
        logger.error(f"Project Creator Agent failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_agent()
