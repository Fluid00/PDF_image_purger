from nicegui import ui

class StyleManager:
    """Manage application styles."""
    
    @staticmethod
    def apply_base_styles():
        """Apply base application styles."""
        ui.add_head_html("""
            <style>
                .folder-row {
                    border: 1px solid #e2e8f0;
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin-bottom: 1rem;
                }
                .directory-label {
                    color: #64748b;
                    font-size: 0.875rem;
                    margin-bottom: 0.25rem;
                }
                .directory-path {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 0.375rem;
                    padding: 0.5rem;
                    font-family: monospace;
                }
                .action-button {
                    min-width: 6rem;
                }
                .progress-container {
                    margin-top: 1rem;
                }
                .messages-log {
                    height: 12rem;
                    border: 1px solid #e2e8f0;
                    border-radius: 0.375rem;
                    padding: 0.5rem;
                    overflow-y: auto;
                    font-family: monospace;
                    font-size: 0.875rem;
                }
            </style>
        """)
