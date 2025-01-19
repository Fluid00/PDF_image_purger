import fitz
import os
import uuid
import logging
from typing import Tuple
from pathlib import Path

logger = logging.getLogger("pdf_purger")

def process_pdf_sync(filepath: str, is_processing: bool) -> Tuple[bool, str]:
    """Synchronous version of PDF processing."""
    file_name = os.path.basename(filepath)
    temp_file = filepath + str(uuid.uuid4()) + ".temp"
    doc = None
    successful = False

    try:
        logger.info(f"Starting processing of {file_name}")
        
        if not is_processing:
            return False, "Processing stopped by user"
        
        # Initial open
        try:
            doc = fitz.open(filepath)
            logger.info(f"Successfully opened {file_name}")
        except Exception as e:
            logger.error(f"Error opening {file_name}: {e}")
            return False, f"Failed to open file: {str(e)}"

        if not is_processing:
            return False, "Processing stopped by user"

        # Process the document
        modified = False
        total_pages = len(doc)
        empty_pages = []
        
        # Find empty pages
        for p_num in range(total_pages):
            if not is_processing:
                return False, "Processing stopped by user"
                
            text = doc[p_num].get_text().strip()
            if not text:
                empty_pages.append(p_num)
                modified = True

        logger.info(f"Found {len(empty_pages)} empty pages in {file_name}")

        # Delete empty pages in reverse order
        for page_num in reversed(empty_pages):
            if not is_processing:
                return False, "Processing stopped by user"
                
            try:
                doc.delete_page(page_num)
                modified = True
                logger.info(f"Deleted page {page_num + 1} in {file_name}")
            except Exception as e:
                logger.warning(f"Error deleting page {page_num + 1} in {file_name}: {e}")

        # Process remaining pages
        remaining_pages = len(doc)
        for p_num in range(remaining_pages):
            if not is_processing:
                return False, "Processing stopped by user"

            page = doc[p_num]
            page_modified = False
            
            # Remove images
            try:
                image_list = page.get_images(True)
                for img in image_list:
                    if not is_processing:
                        return False, "Processing stopped by user"
                    try:
                        page.delete_image(img[0])
                        modified = True
                        page_modified = True
                        logger.info(f"Deleted image {img[0]} on page {p_num + 1} in {file_name}")
                    except Exception as e:
                        logger.warning(f"Error deleting image {img[0]} on page {p_num + 1} in {file_name}: {e}")
            except Exception as e:
                logger.warning(f"Error getting images on page {p_num + 1} in {file_name}: {e}")

            # Fix text colors
            if not is_processing:
                return False, "Processing stopped by user"
            
            try:
                text_blocks = []
                text_dict = page.get_text("dict")
                blocks = text_dict.get('blocks', [])
                for block in blocks:
                    if block.get("type", -1) == 0:  # Text block
                        text_blocks.append(block)

                for block in text_blocks:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span["color"] in (0xFFFFFF, 0xFFFFFF00):  # White text
                                page.insert_text(
                                    fitz.Rect(span["bbox"]).tl,
                                    span["text"],
                                    fontname=span["font"],
                                    fontsize=span["size"],
                                    color=0,  # black
                                    overlay=True
                                )
                                modified = True
                                page_modified = True
            except Exception as e:
                logger.warning(f"Error modifying text colors on page {p_num + 1}: {e}")

            if page_modified:
                logger.info(f"Modified page {p_num + 1} in {file_name}")

        # Save the document if modified
        if modified and is_processing:
            try:
                # Try incremental save first
                doc.save(
                    temp_file,
                    garbage=4,
                    deflate=True,
                    clean=True,
                    linear=True,
                    incremental=True
                )
                
                # Close the current document before replacing
                doc.close()
                doc = None
                
                # Replace the original file
                os.replace(temp_file, filepath)
                successful = True
                logger.info(f"Successfully processed {file_name}")
                
            except Exception as e:
                logger.warning(f"Incremental save failed for {file_name}, trying regular save: {e}")
                try:
                    # If still open, close it
                    if doc:
                        doc.close()
                        doc = None
                        
                    # Try regular save
                    doc = fitz.open(filepath)
                    doc.save(
                        temp_file,
                        garbage=4,
                        deflate=True,
                        clean=True,
                        linear=True,
                        incremental=False
                    )
                    doc.close()
                    doc = None
                    
                    # Replace the original file
                    os.replace(temp_file, filepath)
                    successful = True
                    logger.info(f"Successfully processed {file_name} with regular save")
                    
                except Exception as save_e:
                    logger.error(f"All save attempts failed for {file_name}: {save_e}")
                    return False, f"Failed to save file: {str(save_e)}"
        else:
            successful = True  # If no modifications were needed
            logger.info(f"No modifications needed for {file_name}")

    except Exception as e:
        logger.error(f"Error processing {file_name}: {e}")
        return False, f"Error processing {file_name}: {str(e)}"

    finally:
        # Clean up
        if doc:
            try:
                doc.close()
            except:
                pass
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        logger.info(f"Finished processing {file_name}, successful: {successful}")

    return successful, f"Successfully processed {file_name}" if successful else f"Failed to process {file_name}"
