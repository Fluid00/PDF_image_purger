from pathlib import Path
from nicegui import ui, app
from .style_manager import StyleManager
from .progress_ui import ProgressUI
import logging
import asyncio

logger = logging.getLogger("pdf_purger")

class ProcessPage:
    """Handles the processing status page."""
    def __init__(self, app_instance):
        self.app_instance = app_instance

    async def create_process_ui(self, folder_path: str):
        """Create processing status UI for a specific folder."""
        
        with ui.column().classes('w-full max-w-4xl mx-auto p-4'):
            # Header with back button
            with ui.row().classes('w-full items-center mb-4'):
                ui.button(icon='arrow_back', on_click=lambda: self.show_main_page()).classes('back-button')
                ui.label(f'Processing: {Path(folder_path).name}').classes('text-xl font-bold ml-4')
            
            # Progress components
            progress_ui = ProgressUI()
            
            # Control buttons
            with ui.row().classes('w-full justify-end gap-2 mb-4'):
                ui.button('Stop', on_click=self.app_instance.process_manager.stop_processing).classes('bg-red-500')
                ui.button('Start Processing', on_click=lambda: self.start_processing(folder_path, progress_ui)).classes('bg-green-500')

    async def start_processing(self, folder_path: str, progress_ui: ProgressUI):
        """Start processing after page is loaded."""
        # Add a small delay to ensure WebSocket connection is established
        await asyncio.sleep(0.1)
        try:
            # Use default thread count of 4 since we don't have access to control panel on this page
            await self.app_instance.process_folder(folder_path, progress_ui, 4)
        except Exception as e:
            logger.error(f"Error in process page: {e}")
            ui.notify(f'Error: {str(e)}', type='negative')

    def show_main_page(self):
        """Show the main folder management UI."""
        self.app_instance.index_page.current_folder_path = None
        ui.update(self.app_instance.index_page.initialize_page)
