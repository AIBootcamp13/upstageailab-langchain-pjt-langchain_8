# src/prompt_loader.py
import yaml
from src.config import ROOT_DIR

def load_prompt(prompt_name: str) -> str:
    """Loads a prompt from the YAML file by its name."""
    prompts_path = ROOT_DIR / "prompts" / "blog_prompts.yaml"
    try:
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)
        return prompts[prompt_name]
    except (FileNotFoundError, KeyError) as e:
        print(f"Error loading prompt '{prompt_name}': {e}")
        return "" # Return empty string or raise an exception