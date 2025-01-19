from nicegui import ui, app
from pathlib import Path
from typing import Dict
from .progress_ui import ProgressUI
from .folder_picker_dialog import FolderPickerDialog

class FolderRow:
    """Manage folder row UI components."""
    
    def __init__(self, folder_path: str, on_update, on_remove):
        self.folder_path = folder_path
        self.on_update = on_update
        self.on_remove = on_remove
        self.progress_ui = None
        self.container = None
        self.setup_row()

    def setup_row(self):
        """Setup folder row components."""
        self.container = ui.column().classes('folder-row')
        
        with self.container:
            # Directory section
            with ui.column():
                ui.label('Directory:').classes('directory-label')
                with ui.row().classes('w-full items-center gap-2'):
                    display_name = Path(self.folder_path).name or self.folder_path
                    path_label = ui.label(display_name).classes('directory-path flex-grow')
                    
                    async def browse():
                        picker = FolderPickerDialog(self.folder_path)
                        result = await picker
                        if result:
                            self.folder_path = result[0]
                            path_label.text = Path(result[0]).name or result[0]
                            await self.on_update(self)

                    ui.button('Browse', on_click=browse).classes('action-button')

            # Action buttons
            with ui.row().classes('w-full justify-between mt-4'):
                with ui.row().classes('gap-2'):
                    ui.button('Process', on_click=lambda: self.on_update(self)).classes('action-button').props('primary')
                    ui.button('Remove', on_click=lambda: self.on_remove(self)).classes('action-button')

            # Progress section
            self.progress_ui = ProgressUI()

    def update_progress(self, progress_data: Dict):
        """Update progress display."""
        if self.progress_ui:
            self.progress_ui.update(progress_data)

    def clear_progress(self):
        """Clear progress display."""
        if self.progress_ui:
            self.progress_ui.clear()
