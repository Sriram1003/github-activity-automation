import random
import requests
from utils.logger import setup_logger

logger = setup_logger("ai_client")

class ProjectIdeaGenerator:
    def __init__(self, fallback_ideas: list, hf_token: str = "", model: str = "mistralai/Mistral-7B-Instruct-v0.2", timeout: int = 10):
        self.fallback_ideas = fallback_ideas
        self.hf_token = hf_token
        self.model = model
        self.timeout = timeout

    def _get_fallback_idea(self) -> tuple[str, str]:
        """Returns a random idea from the fallback list."""
        idea = random.choice(self.fallback_ideas)
        # Generate a generic slug from the idea
        words = idea.replace(".", "").split()
        slug = "-".join(words[:4]).lower() + f"-{random.randint(100, 999)}"
        return slug, idea

    def generate_project_idea(self) -> tuple[str, str]:
        """
        Attempts to generate a project idea using the HuggingFace Inference API.
        If it fails, it degrades gracefully to a fallback idea.
        Returns: (project_name_slug, project_description)
        """
        if not self.hf_token:
            logger.info("No HuggingFace token provided. Using built-in fallback ideas.")
            return self._get_fallback_idea()

        api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        
        prompt = "Generate a short, creative idea for a new open-source software project. Return only the description in one sentence."
        payload = {
            "inputs": f"[INST] {prompt} [/INST]",
            "parameters": {"max_new_tokens": 50, "return_full_text": False}
        }

        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                idea_text = data[0]["generated_text"].strip()
                if idea_text:
                    # Create a simple slug from the first few words
                    words = [w for w in idea_text.replace(".", "").replace(",", "").split() if w.isalnum()]
                    slug = "-".join(words[:4]).lower() + f"-{random.randint(100, 999)}"
                    logger.info(f"Successfully generated idea from AI: {slug}")
                    return slug, idea_text
        except requests.exceptions.RequestException as e:
            logger.warning(f"External AI API failed: {e}. Falling back to built-in ideas.")
        except Exception as e:
            logger.warning(f"Unexpected error with AI API: {e}. Falling back.")

        return self._get_fallback_idea()
