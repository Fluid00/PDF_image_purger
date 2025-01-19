import os
    import json
    import logging
    import asyncio
    from pathlib import Path
    from typing import List, Dict
    from process_manager import ProcessManager
    from pdf_processor.core import process_pdf
    from core.file_scanner import FileScanner
    from core.file_tracker import FileTracker
    from core.progress_manager import ProgressManager
    from nicegui import app, ui, run

    logger = logging.getLogger("pdf_purger")

    async def process_pdf_folder(folder_path: str, thread_count: int, progress_callback, process_manager: ProcessManager):
        """
        Process a folder of PDF files with proper async/await handling.
        """
        progress_manager = ProgressManager()
        file_tracker = FileTracker(folder_path)

        success, prep_message = await FileScanner.prepare_folders(folder_path)
        if not success:
            progress_manager.add_message(prep_message, "error")
            progress_callback({'message': prep_message, 'type': 'error'})
            return False, prep_message

        await FileScanner.cleanup_temp_files(folder_path)

        file_list, scan_messages = await FileScanner.scan_pdfs(folder_path, file_tracker)
        for msg in scan_messages:
            progress_manager.add_message(msg)
            progress_callback({'message': msg, 'type': 'info'})

        total_files = len(file_list)
        if not total_files:
            msg = "No new PDF files found to process."
            progress_manager.add_message(msg, "warning")
            progress_callback({'message': msg, 'type': 'warning'})
            return True, msg

        progress_manager.start_batch(total_files)
        progress_callback({
            'progress': 0,
            'text': f"Starting to process {total_files} files",
            'type': 'progress'
        })
