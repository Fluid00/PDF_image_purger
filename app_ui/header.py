from nicegui import ui

class Header:
    """Manage application header."""
    
    @staticmethod
    def create():
        """Create header components."""
        with ui.column().classes('w-full text-center mb-6'):
            ui.label('PDF Purger').classes('text-2xl font-bold mb-2')
            ui.label('Removes images and vector graphics while ensuring text visibility') \
                .classes('text-gray-600')
