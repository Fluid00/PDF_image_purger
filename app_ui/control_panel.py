from nicegui import ui
from typing import Optional

class ControlPanel:
    """Manage application control panel."""
    
    def __init__(self, on_start_all, on_stop_all, on_reset):
        self.thread_count = None  # Will be initialized in setup_panel
        self.on_start_all = on_start_all
        self.on_stop_all = on_stop_all
        self.on_reset = on_reset
        self.container = None
        self.setup_panel()

    def setup_panel(self):
        """Setup control panel components."""
        self.container = ui.row().classes('w-full justify-between items-center p-4 bg-gray-50 rounded-lg')
        
        with self.container:
            # Action buttons on the left
            with ui.row().classes('gap-4'):
                ui.button('Start All', on_click=self.on_start_all) \
                    .props('primary') \
                    .classes('action-button')
                    
                ui.button('Stop All', on_click=self.on_stop_all) \
                    .props('negative') \
                    .classes('action-button')
                    
                ui.button('Reset', on_click=self.on_reset) \
                    .classes('action-button')

            # Thread control on the right
            with ui.row().classes('gap-2 items-center'):
                ui.label('Threads:')
                self.thread_count = ui.number(value=4, min=1, max=16).props('size=sm')
