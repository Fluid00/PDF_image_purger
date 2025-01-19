from nicegui import ui, app
from typing import Dict
import asyncio

class ProgressUI:
    """Manage progress display components."""
    
    def __init__(self):
        self.progress_bar = None
        self.status_label = None
        self.messages_log = None
        self.progress_data = {} # Store the latest progress data here
        self.setup_components()
        self.sync_from_storage()

    def setup_components(self):
        """Setup progress UI components."""
        with ui.column().classes('w-full gap-2 progress-container'):
            self.progress_bar = ui.linear_progress(value=0).props('rounded')
            self.status_label = ui.label().classes('text-sm text-gray-600')
            self.messages_log = ui.log().classes('messages-log')

    def update(self, progress_data: Dict = None):
        """Update progress display."""
        if progress_data:
            self.progress_data = progress_data # Store the latest data

        if 'progress' in self.progress_data:
            self.progress_bar.value = self.progress_data['progress']
        
        if 'message' in self.progress_data:
            message = self.progress_data['message']
            message_type = self.progress_data.get('type', 'info')
            
            prefix = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'success': '✅'
            }.get(message_type, '')
            
            formatted_message = f"{prefix} {message}" if prefix else message
            self.messages_log.push(formatted_message)
            
            if message_type != 'progress':
                self.status_label.text = message
        
        # Sync to storage
        asyncio.create_task(self._sync_to_storage())

    def clear(self):
        """Clear progress display."""
        self.progress_bar.value = 0
        self.status_label.text = ""
        self.messages_log.clear()
        asyncio.create_task(self._sync_to_storage())

    def sync_from_storage(self):
        """Sync progress state from storage on reconnection."""
        try:
            state = app.storage.user.get('progress_state', {})
            if state:
                self.progress_bar.value = state.get('progress', 0.0)
                self.status_label.text = state.get('text', '')
                self.messages_log.clear()
                for message in state.get('messages', []):
                    self.messages_log.push(message)
        except RuntimeError:
            pass  # Not in page context
            
    async def _sync_to_storage(self):
        """Sync progress state to storage."""
        try:
            app.storage.user['progress_state'] = {
                'progress': self.progress_bar.value,
                'text': self.status_label.text,
                'messages': []  # Messages are not stored in storage as they are ephemeral
            }
        except RuntimeError:
            pass  # Not in page context
