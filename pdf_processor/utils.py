import fitz
import logging
from nicegui import run

logger = logging.getLogger("pdf_purger")

def repair_xrefs(doc: fitz.Document) -> bool:
    """Repair cross-references in PDF document."""
    try:
        if hasattr(doc, 'xref_repair'):
            doc.xref_repair()
        if hasattr(doc, 'xref_compress'):
            doc.xref_compress()
        return True
    except Exception as e:
        logger.warning(f"Warning during xref repair: {e}")
        return False

def replace_white_with_black(page: fitz.Page):
    """Replace white text with black text."""
    try:
        text_blocks = []
        try:
            text_dict = page.get_text("dict")
            blocks = text_dict.get('blocks', [])
            for block in blocks:
                if block.get("type", -1) == 0:  # Text block
                    text_blocks.append(block)
        except Exception as e:
            logger.warning(f"Error getting text blocks on page {page.number + 1}: {e}")

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
    except Exception as e:
        logger.warning(f"Error modifying text colors on page {page.number + 1}: {e}")
