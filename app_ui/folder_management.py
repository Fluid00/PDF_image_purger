import asyncio
from pathlib import Path
from typing import List, Dict
from nicegui import app, ui, run
from .folder_row import FolderRow
from .folder_picker_dialog import FolderPickerDialog
from core.state_manager import save_state
from .progress_ui import ProgressUI
import logging
import os

logger = logging.getLogger("pdf_purger")

class FolderManagement:
    """Manages folder rows and related actions."""
    def __init__(self, app_instance):
        self.app_instance = app_instance
        self.folder_rows: List[FolderRow] = []

    async def setup_folder_management(self):
        """Setup folder management UI and components."""
        with ui.column().classes('w-full gap-4'):
            ui.label('Folder Management').classes('text-xl font-bold mt-6 mb-2')
            
            # Create rows for existing folders
            for folder_path in app.storage.user['folder_paths']:
                await self.add_folder_row(folder_path)
            
            # Add Folder button
            with ui.row().classes('w-full justify-center mt-4'):
                async def browse_and_add():
                    picker = FolderPickerDialog(directory=".", multiple=False)
                    result = await picker
                    if result:
                        await self.add_folder_row(result[0])
                ui.button('Add Folder', 
                         on_click=browse_and_add,
                         icon='add').classes('w-1/3')

    async def add_folder_row(self, folder_path: str = ""):
        """Add a new folder row to the UI."""
        row = FolderRow(
            folder_path=folder_path,
            on_update=self.handle_folder_update,
            on_remove=self.handle_folder_remove
        )
        self.folder_rows.append(row)
        
        # Update storage state if folder_path provided
        if folder_path:
            paths = list(app.storage.user['folder_paths'])
            if folder_path not in paths:
                paths.append(folder_path)
                app.storage.user['folder_paths'] = paths
                self.app_instance._folder_paths = paths.copy()
                await run.io_bound(save_state, paths)

    async def handle_folder_update(self, folder_row: FolderRow):
        """Handle folder update request."""
        logger.info(f"Handling folder update for {folder_row.folder_path}")
        if self.app_instance.process_manager.is_processing():
            ui.notify('Please stop current processing first', 
                     type='warning')
            return
            
        if not folder_row.folder_path:
            ui.notify('Please select a folder first', 
                     type='warning')
            return
        
        folder_path = os.path.abspath(folder_row.folder_path)
        
        # Update storage state
        paths = list(app.storage.user['folder_paths'])
        
        if folder_path not in paths:
            paths.append(folder_path)
        else:
            # Ensure correct index
            index = paths.index(folder_path)
            paths[index] = folder_path
        
        app.storage.user['folder_paths'] = paths
        self.app_instance._folder_paths = paths.copy()
        await run.io_bound(save_state, paths)

        # Start processing
        thread_count = self.app_instance.index_page.control_panel.thread_count.value if self.app_instance.index_page.control_panel else 4
        await self.app_instance.process_folder(folder_path, folder_row.progress_ui, thread_count)

    async def handle_folder_remove(self, folder_row: FolderRow):
        """Handle folder removal request."""
        if self.app_instance.process_manager.is_processing():
            await self.app_instance.process_manager.stop_processing()
            await asyncio.sleep(0.5)
            
        # Update storage state
        paths = list(app.storage.user['folder_paths'])
        if folder_row.folder_path in paths:
            paths.remove(folder_row.folder_path)
            app.storage.user['folder_paths'] = paths
            self.app_instance._folder_paths = paths.copy()
            await run.io_bound(save_state, paths)
            
        # Remove from UI
        if folder_row in self.folder_rows:
            self.folder_rows.remove(folder_row)
            folder_row.container.clear()
            ui.notify(f'Removed folder: {Path(folder_row.folder_path).name}',
                     type='info')

    async def start_all_folders(self):
        """Start processing all folders concurrently."""
        paths = app.storage.user['folder_paths']
        if not paths:
            ui.notify('No folders to process', type='warning')
            return
            
        if self.app_instance.process_manager.is_processing():
             ui.notify('Processing already in progress', type='warning')
             return

        thread_count = self.app_instance.index_page.control_panel.thread_count.value if self.app_instance.index_page.control_panel else 4
        
        # Create tasks for all folders
        self.app_instance.current_tasks = [
            asyncio.create_task(self.app_instance.process_folder(folder_path, FolderRow(folder_path, None, None).progress_ui, thread_count))
            for folder_path in paths
        ]
        self.app_instance.process_manager.start_processing()

        # Wait for all tasks to complete and reset state
        await asyncio.gather(*self.app_instance.current_tasks, return_exceptions=True)
        self.app_instance.process_manager.reset()

    async def stop_all_processing(self):
        """Stop all current processing."""
        logger.info("Stop all processing requested")
        if self.app_instance.process_manager.stop_processing():
            ui.notify('Processing stopped', type='warning')
            if self.app_instance.current_tasks:
                for task in self.app_instance.current_tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*self.app_instance.current_tasks, return_exceptions=True)
                self.app_instance.current_tasks = []
        await asyncio.sleep(0.5)
        ui.navigate.to('/')

    async def reset_state(self):
        """Reset application state."""
        await self.app_instance.process_manager.stop_processing()
        app.storage.user['folder_paths'] = []
        app.storage.user['progress_state'] = {}
        self.app_instance._folder_paths = []
        await run.io_bound(save_state, [])
        ui.notify('Application state reset', type='info')
        ui.navigate.reload()
