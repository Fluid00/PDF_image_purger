from typing import Optional
from nicegui import app, ui
from app_ui.control_panel import ControlPanel
from app_ui.header import Header
from app_ui.style_manager import StyleManager
from app_ui.folder_picker_dialog import FolderPickerDialog
from app_ui.folder_management import FolderManagement
from core.state_manager import load_state, save_state
import logging

logger = logging.getLogger("pdf_purger")

class IndexPage:
    """Handles the main application page."""
    def __init__(self, app_instance):
        self.app_instance = app_instance
        self.folder_management = None
        self.control_panel = None
        self._folder_paths = load_state()
        
        @ui.page('/')
        async def index_page():
            """Main application page."""
            # Initialize storage when page loads
            if 'processing' not in app.storage.user:
                app.storage.user['processing'] = False
            if 'stop_requested' not in app.storage.user:
                app.storage.user['stop_requested'] = False
            if 'active_folders' not in app.storage.user:
                app.storage.user['active_folders'] = []
            if 'folder_paths' not in app.storage.user:
                app.storage.user['folder_paths'] = self._folder_paths.copy()
            if 'progress_state' not in app.storage.user:
                app.storage.user['progress_state'] = {}
            
            # Sync process manager with storage
            self.app_instance.process_manager.sync_with_storage()
            
            await self.initialize_page()

    async def initialize_page(self):
        """Initialize main page UI and components."""
        StyleManager.apply_base_styles()
        
        with ui.column().classes('w-full max-w-4xl mx-auto p-4'):
            # Header
            Header.create()
            
            # Control Panel
            self.control_panel = ControlPanel(
                on_start_all=self.start_all_folders,
                on_stop_all=self.stop_all_processing,
                on_reset=self.reset_state
            )
            
            # Folder Management Section
            self.folder_management = FolderManagement(self.app_instance)
            await self.folder_management.setup_folder_management()

    async def start_all_folders(self):
        """Start processing all folders concurrently."""
        await self.folder_management.start_all_folders()

    async def stop_all_processing(self):
        """Stop all current processing."""
        await self.folder_management.stop_all_processing()

    async def reset_state(self):
        """Reset application state."""
        await self.folder_management.reset_state()
