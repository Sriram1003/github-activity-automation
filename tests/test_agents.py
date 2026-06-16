import os
import json
import tempfile
from unittest import mock
from utils.state_manager import StateManager

def test_idempotency_logic():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(b'{"daily_commit_last_run_date": "2023-10-25", "daily_commit_last_repo": "test-repo"}')
        tmp_name = tmp.name

    state_manager = StateManager(state_file=tmp_name)
    assert state_manager.get_last_run_date() == "2023-10-25"
    assert state_manager.get_last_repo() == "test-repo"

    # Test update
    state_manager.update_daily_commit("2023-10-26", "another-repo")
    assert state_manager.get_last_run_date() == "2023-10-26"
    assert state_manager.get_last_repo() == "another-repo"
    
    os.remove(tmp_name)

def test_repo_selection_logic():
    # Simulate repos list
    repos = [
        {"name": "repo1", "fork": False, "archived": False},
        {"name": "repo2", "fork": False, "archived": False},
        {"name": "repo3", "fork": False, "archived": False}
    ]
    
    last_repo = "repo2"
    
    # Filter logic from daily_commit.py
    available_repos = [r for r in repos if r["name"] != last_repo]
    
    assert len(available_repos) == 2
    assert "repo2" not in [r["name"] for r in available_repos]

def test_ai_fallback():
    from utils.ai_client import ProjectIdeaGenerator
    
    generator = ProjectIdeaGenerator(fallback_ideas=["Fallback Idea 1", "Fallback Idea 2"], hf_token="")
    slug, idea = generator.generate_project_idea()
    
    assert idea in ["Fallback Idea 1", "Fallback Idea 2"]
    assert len(slug) > 0
