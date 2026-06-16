import base64
import requests
import sys
from datetime import datetime
from typing import List, Dict, Optional
from utils.logger import setup_logger

logger = setup_logger("github_api")

class GitHubAPI:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        })

    def _check_response(self, response: requests.Response) -> requests.Response:
        """Checks for errors and rate limits in the response."""
        if "X-RateLimit-Remaining" in response.headers:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            
            if response.status_code == 403 and remaining == 0:
                reset_timestamp = int(response.headers.get("X-RateLimit-Reset", 0))
                reset_time = datetime.fromtimestamp(reset_timestamp).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
                logger.error(f"GitHub API rate limit exhausted! Resets at: {reset_time}")
                sys.exit(1)
                
            if remaining < 100:
                logger.warning(f"GitHub API rate limit running low: {remaining} requests remaining.")
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"GitHub API HTTP Error: {e} - Response: {response.text}")
            raise
        return response

    def get_authenticated_user(self) -> Dict:
        """Fetches the authenticated user's details."""
        resp = self.session.get(f"{self.BASE_URL}/user")
        return self._check_response(resp).json()

    def get_eligible_repositories(self, username: str) -> List[Dict]:
        """Fetches all non-forked, non-archived repositories for the given user."""
        repos = []
        page = 1
        while True:
            resp = self.session.get(f"{self.BASE_URL}/users/{username}/repos", params={"per_page": 100, "page": page})
            data = self._check_response(resp).json()
            if not data:
                break
            
            for repo in data:
                if not repo.get("fork") and not repo.get("archived"):
                    repos.append(repo)
            page += 1
            
        return repos

    def get_file_info(self, owner: str, repo: str, file_path: str) -> Optional[Dict]:
        """Gets info about a file, including its SHA. Returns None if it doesn't exist."""
        resp = self.session.get(f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path}")
        if resp.status_code == 404:
            return None
        self._check_response(resp)
        return resp.json()

    def create_or_update_file(self, owner: str, repo: str, file_path: str, message: str, content: str, sha: str = None) -> Dict:
        """Creates or updates a file in the repository."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
        
        # Base64 encode the content
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": message,
            "content": encoded_content
        }
        if sha:
            payload["sha"] = sha
            
        resp = self.session.put(url, json=payload)
        return self._check_response(resp).json()

    def create_repository(self, name: str, description: str = "", private: bool = False) -> Dict:
        """Creates a new repository for the authenticated user."""
        url = f"{self.BASE_URL}/user/repos"
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False  # We will manually populate the repo
        }
        resp = self.session.post(url, json=payload)
        return self._check_response(resp).json()
