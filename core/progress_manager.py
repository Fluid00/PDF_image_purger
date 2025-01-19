from typing import Dict, List
import logging
from nicegui import app, run

logger = logging.getLogger("pdf_purger")

class ProgressManager:
    """Handle progress tracking and message management."""
    def __init__(self):
        self.messages: List[str] = []
        self.current_progress: float = 0.0
        self.current_text: str = ""
        self.total_files: int = 0
        self.processed_files: int = 0
        
    def start_batch(self, total_files: int):
        """Initialize for a new batch of files."""
        self.total_files = total_files
        self.processed_files = 0
        self.current_progress = 0.0
        self.messages.clear()
        self._sync_to_storage()
            
    def add_message(self, message: str, message_type: str = "info"):
        """Add a message with optional type (info/warning/error)."""
        prefix = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }.get(message_type, "")
        
        formatted_message = f"{prefix} {message}" if prefix else message
        self.messages.append(formatted_message)
        logger.info(message)
        self._sync_to_storage()
            
    def update_progress(self, progress: float, text: str):
        """Update progress state."""
        self.current_progress = min(max(progress, 0.0), 1.0)
        self.current_text = text
        self._sync_to_storage()
            
    def increment_processed(self):
        """Increment processed files counter and update progress."""
        self.processed_files += 1
        if self.total_files > 0:
            self.current_progress = self.processed_files / self.total_files
        self._sync_to_storage()
                
    def get_state(self) -> Dict:
        """Get current progress state."""
        return {
            'messages': self.messages.copy(),
            'progress': self.current_progress,
            'text': self.current_text,
            'processed': self.processed_files,
            'total': self.total_files
        }
            
    def clear(self):
        """Reset progress state."""
        self.messages.clear()
        self.current_progress = 0.0
        self.current_text = ""
        self.total_files = 0
        self.processed_files = 0
        self._sync_to_storage()

    def _sync_to_storage(self):
        """Sync progress state to storage."""
        try:
            app.storage.user['progress_state'] = self.get_state()
        except RuntimeError:
            pass  # Not in page context

    def sync_from_storage(self):
        """Sync progress state from storage."""
        try:
            state = app.storage.user.get('progress_state', {})
            if state:
                self.messages = state.get('messages', [])
                self.current_progress = state.get('progress', 0.0)
                self.current_text = state.get('text', '')
                self.processed_files = state.get('processed', 0)
                self.total_files = state.get('total', 0)
        except RuntimeError:
            pass  # Not in page context
