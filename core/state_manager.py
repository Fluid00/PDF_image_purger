import json
import logging
from pathlib import Path
from typing import List
from nicegui import run

logger = logging.getLogger("pdf_purger")

def load_state() -> List[str]:
    """Load folder paths from state file."""
    try:
        state_file = Path('purger_state.json')
        if not state_file.exists():
            return []
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
            return state.get('folders', [])
    except Exception as e:
        logger.error(f"Error loading state: {e}")
        return []

def save_state(folder_paths: List[str]):
    """Save folder paths to state file."""
    try:
        state_file = Path('purger_state.json')
        state = {'folders': [str(path) for path in folder_paths if path]}
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving state: {e}")
