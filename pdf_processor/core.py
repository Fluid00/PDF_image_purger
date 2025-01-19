import fitz
import os
import uuid
import logging
import asyncio
from typing import Tuple
from nicegui import app
from pdf_processor.utils import repair_xrefs, replace_white_with_black

logger = logging.getLogger("pdf_purger")

async def process_pdf(filepath: str, progress_callback, process_manager) -> Tuple[bool, str]:
    """Process a single PDF file with proper async handling."""
    file_name = os.path.basename(filepath)
    temp_file = filepath + str(uuid.uuid4()) + ".temp"
    doc = None
    successful = False

    try:
        logger.info(f"Starting processing of {file_name}")
        # Run PDF operations in a thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        
        # Check if processing should stop
        if not process_manager.is_processing():
            return False, "Processing stopped by user"
        
        # Initial open and repair if needed
        try:
            doc = await loop.run_in_executor(None, fitz.open, filepath)
            logger.info(f"Successfully opened {file_name}")
        except Exception as e:
            if not process_manager.is_processing():
                return False, "Processing stopped by user"
                
            logger.warning(f"Error opening {file_name}: {e}, attempting repair")
            doc = await loop.run_in_executor(None, fitz.open, filepath)
            await loop.run_in_executor(None, doc.repair)
            await loop.run_in_executor(None, 
                lambda: doc.save(temp_file,
                    garbage=4,
                    clean=True,
                    deflate=True,
                    pretty=False,
                    linear=True)
            )
            await loop.run_in_executor(None, doc.close)
            
            # Verify repair
            doc = await loop.run_in_executor(None, fitz.open, temp_file)
            os.replace(temp_file, filepath)
            doc = await loop.run_in_executor(None, fitz.open, filepath)
            logger.info(f"Successfully repaired and reopened {file_name}")

        if not process_manager.is_processing():
            return False, "Processing stopped by user"

        if not await loop.run_in_executor(None, repair_xrefs, doc):
            if progress_callback:
                progress_callback({
                    'type': 'warning',
                    'message': f"Initial xref repair failed for {file_name}"
                })
            logger.warning(f"Initial xref repair failed for {file_name}")

        # Get total pages and empty pages
        total_pages = len(doc)
        empty_pages = []
        
        # Find empty pages
        for p_num in range(total_pages):
            if not process_manager.is_processing():
                return False, "Processing stopped by user"
                
            text = await loop.run_in_executor(None, lambda: doc[p_num].get_text().strip())
            if not text:
                empty_pages.append(p_num)
            await asyncio.sleep(0) # Yield to the event loop after each page check
        logger.info(f"Found {len(empty_pages)} empty pages in {file_name}")

        # Delete empty pages in reverse order
        for page_num in reversed(empty_pages):
            if not process_manager.is_processing():
                return False, "Processing stopped by user"
                
            try:
                await loop.run_in_executor(None, doc.delete_page, page_num)
                logger.info(f"Deleted page {page_num + 1} in {file_name}")
            except Exception as e:
                logger.warning(f"Error deleting page {page_num + 1} in {file_name}: {e}")
            await asyncio.sleep(0) # Yield after each page deletion

        # Process remaining pages
        for p_num in range(len(doc)):
            if not process_manager.is_processing():
                return False, "Processing stopped by user"

            page = doc[p_num]
            
            # Remove images
            try:
                image_list = await loop.run_in_executor(None, page.get_images, True)
                for img in image_list:
                    if not process_manager.is_processing():
                        return False, "Processing stopped by user"
                    try:
                        await loop.run_in_executor(None, page.delete_image, img[0])
                        logger.info(f"Deleted image {img[0]} on page {p_num + 1} in {file_name}")
                    except Exception as e:
                        logger.warning(f"Error deleting image {img[0]} on page {p_num + 1} in {file_name}: {e}")
                    await asyncio.sleep(0) # Yield after each image deletion
            except Exception as e:
                logger.warning(f"Error getting images on page {p_num + 1} in {file_name}: {e}")

            # Fix text colors
            if not process_manager.is_processing():
                return False, "Processing stopped by user"
            await loop.run_in_executor(None, replace_white_with_black, page)
            await asyncio.sleep(0) # Yield after each page processing

        # Final
