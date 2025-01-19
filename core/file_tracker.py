from typing import Set
from pathlib import Path
from nicegui import run

class FileTracker:
    """Track processed and skipped files."""
    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path)
        self.purged_files = self._load_file_set("purged_files.txt")
        self.skipped_files = self._load_file_set("skipped_files.txt")
        
    def _load_file_set(self, filename: str) -> Set[str]:
        """Load a set of files from tracking file."""
        file_path = self.folder_path / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                return {line.strip() for line in f if line.strip()}
        return set()
        
    def _save_to_file(self, filename: str, file_path: str):
        """Save a file path to tracking file."""
        with open(self.folder_path / filename, 'a') as f:
            f.write(f"{file_path}\n")
            
    def is_processed(self, file_path: str) -> bool:
        """Check if file has been processed or skipped."""
        return (file_path in self.purged_files or 
                file_path in self.skipped_files)
            
    def mark_purged(self, file_path: str):
        """Mark file as successfully purged."""
        if file_path not in self.purged_files:
            self.purged_files.add(file_path)
            run.io_bound(self._save_to_file, "purged_files.txt", file_path)
            
    def mark_skipped(self, file_path: str):
        """Mark file as skipped."""
        if file_path not in self.skipped_files:
            self.skipped_files.add(file_path)
            run.io_bound(self._save_to_file, "skipped_files.txt", file_path)
