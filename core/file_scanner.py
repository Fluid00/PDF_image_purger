import os
from pathlib import Path
from typing import List, Tuple
from core.file_tracker import FileTracker
import logging
import asyncio
from nicegui import run

logger = logging.getLogger("pdf_purger")

class FileScanner:
    """Handle file scanning and validation."""
    
    @staticmethod
    async def scan_pdfs(folder_path: str, file_tracker: FileTracker) -> Tuple[List[str], List[str]]:
        """Scan folder and all subfolders for PDFs to process."""
        file_list = []
        messages = []
        loop = asyncio.get_running_loop()
        
        try:
            # Run the file scanning in a thread pool
            def scan_directory():
                files = []
                for root, _, files_in_dir in os.walk(folder_path):
                    for file in files_in_dir:
                        if file.lower().startswith("bilag_") and file.lower().endswith(".pdf"):
                            file_path = os.path.join(root, file)
                            if not file_tracker.is_processed(file_path):
                                files.append(file_path)
                return files

            # Execute the scan in a thread pool
            file_list = await run.io_bound(scan_directory)

            messages.extend([
                f"Found {len(file_list)} new PDF files to process",
                f"({len(file_tracker.purged_files)} previously processed, "
                f"{len(file_tracker.skipped_files)} skipped)"
            ])

        except Exception as e:
            logger.error(f"Error scanning folder {folder_path}: {e}")
            messages.append(f"Error scanning folder: {str(e)}")
            
        # Yield control back to the event loop
        await asyncio.sleep(0)
        return file_list, messages

    @staticmethod
    async def prepare_folders(folder_path: str) -> Tuple[bool, str]:
        """Prepare folder structure for processing."""
        loop = asyncio.get_running_loop()
        
        try:
            def prepare():
                folder = Path(folder_path)
                
                # Create main folder if it doesn't exist
                folder.mkdir(parents=True, exist_ok=True)
                
                # Create required subfolders
                (folder / "to_delete").mkdir(exist_ok=True)
                (folder / "logs").mkdir(exist_ok=True)
                
                # Initialize tracking files if they don't exist
                for track_file in ["purged_files.txt", "skipped_files.txt"]:
                    track_path = folder / track_file
                    if not track_path.exists():
                        track_path.touch()
                            
                return True, "Folder structure prepared successfully"

            # Execute the preparation in a thread pool
            success, message = await run.io_bound(prepare)
            return success, message
                
        except Exception as e:
            logger.error(f"Error preparing folders: {e}")
            return False, f"Error preparing folders: {str(e)}"

    @staticmethod
    async def cleanup_temp_files(folder_path: str):
        """Remove temporary files from previous runs."""
        loop = asyncio.get_running_loop()
        
        try:
            def cleanup():
                folder = Path(folder_path)
                for item in folder.rglob("*.temp"):
                    try:
                        item.unlink()
                    except Exception as e:
                        logger.warning(f"Could not delete temp file {item}: {e}")

            # Execute the cleanup in a thread pool
            await run.io_bound(cleanup)
                
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")

    @staticmethod
    async def validate_folder(folder_path: str) -> Tuple[bool, str]:
        """Validate folder path and accessibility."""
        loop = asyncio.get_running_loop()
        
        try:
            def validate():
                folder = Path(folder_path)
                if not folder.exists():
                    return False, "Folder does not exist"
                if not folder.is_dir():
                    return False, "Path is not a directory"
                # Test write permissions by trying to create a test file
                test_file = folder / ".test_write_permission"
                try:
                    test_file.touch()
                    test_file.unlink()
                except Exception:
                    return False, "No write permission in folder"
                return True, "Folder is valid and accessible"

            # Execute the validation in a thread pool
            return await run.io_bound(validate)
                
        except Exception as e:
            return False, f"Error validating folder: {str(e)}"

    @staticmethod
    async def get_folder_stats(folder_path: str, file_tracker: FileTracker) -> dict[str, int]:
        """Get folder statistics."""
        loop = asyncio.get_running_loop()
        
        try:
            def calculate_stats():
                stats = {
                    'total_files': 0,
                    'processed_files': len(file_tracker.purged_files),
                    'skipped_files': len(file_tracker.skipped_files),
                    'pending_files': 0
                }
                
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().startswith("bilag_") and file.lower().endswith(".pdf"):
                            stats['total_files'] += 1
                                
                stats['pending_files'] = (
                    stats['total_files'] 
                    - stats['processed_files'] 
                    - stats['skipped_files']
                )
                
                return stats

            # Execute the stats calculation in a thread pool
            return await run.io_bound(calculate_stats)
                
        except Exception as e:
            logger.error(f"Error getting folder stats: {e}")
            return {
                'total_files': 0,
                'processed_files': 0,
                'skipped_files': 0,
                'pending_files': 0
            }
