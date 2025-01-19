from typing import Set
from nicegui import app, ui

class ProcessManager:
    """Handle process state management and concurrency control."""
    def __init__(self):
        self._processing = False
        self._stop_requested = False
        self._active_folders = set()
        
    def start_processing(self, folder_path: str = None) -> bool:
        """Start processing with optional folder tracking."""
        if self.is_processing():
            return False
            
        self._processing = True
        self._stop_requested = False
        
        if folder_path:
            self._active_folders.add(folder_path)

        # Update storage if in page context
        try:
            app.storage.user['processing'] = True
            app.storage.user['stop_requested'] = False
            app.storage.user['active_folders'] = list(self._active_folders)
        except RuntimeError:
            pass
            
        return True
        
    def stop_processing(self) -> bool:
        """Request processing stop with notification."""
        if not self.is_processing():
            return False
            
        self._processing = False  # Changed this to immediately stop processing
        self._stop_requested = True
        
        # Update storage if in page context
        try:
            app.storage.user['processing'] = False
            app.storage.user['stop_requested'] = True
        except RuntimeError:
            pass
            
        ui.notify("Processing will stop", 
                 color="warning", 
                 position="top")
        return True
        
    def reset(self):
        """Reset all process state."""
        self._processing = False
        self._stop_requested = False
        self._active_folders = set()
        
        # Update storage if in page context
        try:
            app.storage.user['processing'] = False
            app.storage.user['stop_requested'] = False
            app.storage.user['active_folders'] = []
        except RuntimeError:
            pass
            
    def is_processing(self) -> bool:
        """Check if processing is currently active."""
        return self._processing
        
    def is_stop_requested(self) -> bool:
        """Check if processing stop has been requested."""
        return self._stop_requested
        
    def sync_with_storage(self):
        """Sync process state with storage on reconnection."""
        try:
            self._processing = app.storage.user.get('processing', False)
            self._stop_requested = app.storage.user.get('stop_requested', False)
            self._active_folders = set(app.storage.user.get('active_folders', []))
        except RuntimeError:
            pass  # Not in page context
