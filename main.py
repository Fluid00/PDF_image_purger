import os
import logging
from nicegui import app, ui, run
from app_ui.index_page import IndexPage
from app_ui.process_page import ProcessPage
from process_manager import ProcessManager
from core.file_scanner import FileScanner
from core.file_tracker import FileTracker
from core.progress_manager import ProgressManager
from pdf_processor.processor import process_pdf_sync
from core.state_manager import load_state
from typing import Dict
import asyncio
from asyncio import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_purger.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pdf_purger")

class App:
    """Main application class."""
    def __init__(self):
        self.process_manager = ProcessManager()
        self.current_tasks = []
        self._folder_paths = load_state()
        self.index_page = None
        self.ui_queue = Queue()

    async def process_folder(self, folder_path: str, progress_ui, thread_count: int):
        """Process a folder of PDF files."""
        progress_manager = ProgressManager()
        file_tracker = FileTracker(folder_path)

        success, prep_message = await FileScanner.prepare_folders(folder_path)
        if not success:
            progress_manager.add_message(prep_message, "error")
            progress_ui.update({'message': prep_message, 'type': 'error'})
            await asyncio.sleep(0)  # Yield to the event loop
            return False, prep_message

        await FileScanner.cleanup_temp_files(folder_path)

        file_list, scan_messages = await FileScanner.scan_pdfs(folder_path, file_tracker)
        for msg in scan_messages:
            progress_manager.add_message(msg)
            progress_ui.update({'message': msg, 'type': 'info'})
            await asyncio.sleep(0)  # Yield to the event loop

        total_files = len(file_list)
        if not total_files:
            msg = "No new PDF files found to process."
            progress_manager.add_message(msg, "warning")
            progress_ui.update({'message': msg, 'type': 'warning'})
            await asyncio.sleep(0)  # Yield to the event loop
            return True, msg

        progress_manager.start_batch(total_files)
        progress_ui.update({
            'progress': 0,
            'text': f"Starting to process {total_files} files",
            'type': 'progress'
        })
        await asyncio.sleep(0)  # Yield to the event loop
        
        self.process_manager.start_processing(folder_path)

        # Use asyncio.Semaphore for throttling
        semaphore = asyncio.Semaphore(thread_count)
        
        async def process_file(file_path: str):
            async with semaphore:
                await self._process_file_with_retry(file_path, progress_ui, file_tracker, progress_manager)

        # Create tasks for all files
        tasks = [process_file(file_path) for file_path in file_list]

        # Process files concurrently with proper cancellation handling
        try:
            await asyncio.gather(*tasks)
            logger.info(f"All tasks completed for {folder_path}")
        except asyncio.CancelledError:
            logger.info(f"Processing cancelled for {folder_path}")
            raise
        finally:
            self.process_manager.reset()
            logger.info(f"Processing reset for {folder_path}")

        if not self.process_manager.is_processing():
            return False, "Processing stopped by user"
        
        final_msg = f"Successfully processed {progress_manager.processed_files} out of {total_files} files"
        progress_ui.update({'message': final_msg, 'type': 'success'})
        await asyncio.sleep(0)  # Yield to the event loop
        return progress_manager.processed_files > 0, final_msg

    async def _process_file_with_retry(self, file_path: str, progress_ui, file_tracker, progress_manager):
        """Process a single file with retry logic."""
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                # Changed to use sync version with run.cpu_bound
                success, message = await run.cpu_bound(
                    process_pdf_sync,
                    file_path,
                    self.process_manager.is_processing()
                )
                
                # Handle the result
                if success:
                    file_tracker.mark_purged(file_path)
                    progress_manager.processed_files += 1
                    progress_ui.update({
                        'message': message,
                        'type': 'success'
                    })
                else:
                    file_tracker.mark_skipped(file_path)
                    if "stopped by user" not in message:
                        progress_ui.update({
                            'message': message,
                            'type': 'error'
                        })

                # Update progress after each file
                progress = progress_manager.processed_files / progress_manager.total_files
                progress_ui.update({
                    'progress': progress,
                    'text': f"Processed {progress_manager.processed_files}/{progress_manager.total_files} files",
                    'type': 'progress'
                })
                await asyncio.sleep(0)  # Yield after each file
                return

            except Exception as e:
                logger.error(f"Attempt {attempt} failed for {file_path}: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Max retries reached for {file_path}. Skipping.")
                    progress_ui.update({
                        'message': f"Failed to process {os.path.basename(file_path)} after multiple retries.",
                        'type': 'error'
                    })
                    file_tracker.mark_skipped(file_path)
                    await asyncio.sleep(0)  # Yield after failure

    async def process_ui_queue(self):
        """Process UI update messages from the queue."""
        while True:
            try:
                message = await self.ui_queue.get()
                await ui.run_javascript(message, timeout=5.0)
                self.ui_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing UI queue: {e}")

async def initialize_app():
    """Initialize the application."""
    # Generate random secret for storage
    storage_secret = os.urandom(16).hex()

    try:
        # Initialize application
        app_instance = App()
        index_page = IndexPage(app_instance)
        process_page = ProcessPage(app_instance)
        app_instance.index_page = index_page

        logger.info("Application initialized successfully")
        
        # Create the task here, after the event loop is running
        asyncio.create_task(app_instance.process_ui_queue())
        
        @ui.page('/process/{folder_path}')
        async def process_page_route(folder_path: str):
            """Route for the process page."""
            await process_page.create_process_ui(folder_path)

    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        raise

if __name__ in {"__main__", "__mp_main__"}:
    def startup():
        loop = asyncio.get_running_loop()
        loop.set_debug(True)
        loop.slow_callback_duration = 0.05

    app.on_startup(startup)
    app.on_startup(initialize_app)
    
    ui.run(
        storage_secret=os.urandom(16).hex(),
        title="PDF Purger",
        favicon="📄",
        dark=False,
        reload=False,
        port=8080,
    )
