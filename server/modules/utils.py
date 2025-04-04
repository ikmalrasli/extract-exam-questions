import fitz
import os

def get_last_page(pdf_content: bytes) -> int:
    """Returns the last page number of a PDF."""
    doc = fitz.open(stream=pdf_content, filetype="pdf")  # Open PDF from bytes
    last_page = len(doc)  # Get total page count
    doc.close()
    return last_page

def get_reference_pdf() -> str:
    """Get the reference PDF content."""
    reference_pdf_path = 'reference_files/reference_input.pdf'
    
    if not os.path.exists(reference_pdf_path):
        raise ValueError(f"Reference PDF not found: {reference_pdf_path}")
        
    with open(reference_pdf_path, 'rb') as f:
        return f.read()

def is_pdf_rasterized(pdf_content: bytes) -> bool:
    """Checks if a PDF byte stream is likely rasterized."""
    try:
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text = page.get_text("text")
            if text.strip():
                pdf_document.close()
                return False
            images = page.get_images(full=True)
            if not images:
                pdf_document.close()
                return False
        pdf_document.close()
        return True
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return False

def get_rasterized_pdf(pdf_content: bytes):
    #First, check if pdf is rasterized. If rasterized, return the pdf.
    if is_pdf_rasterized(pdf_content):
        print(f"PDF is already rasterized.")
        return pdf_content
    else:
        print(f"PDF is not rasterized. Rasterizing...")
        # If not rasterized, then rasterize the pdf.
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        rasterized_pdf_stream = fitz.open()  # Create a new PDF to hold rasterized pages
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)  # Load each page
            pix = page.get_pixmap()  # Render page to a pixmap (image)
            rasterized_page = rasterized_pdf_stream.new_page(width=pix.width, height=pix.height)  # Create a new page in the rasterized PDF
            rasterized_page.insert_image(rasterized_page.rect, pixmap=pix)  # Insert the image into the new page
        
        # Save the rasterized PDF to bytes
        rasterized_pdf_bytes = rasterized_pdf_stream.write()
        print(f"PDF rasterization complete.")
        
        rasterized_pdf_stream.close()
        pdf_document.close()
        return rasterized_pdf_bytes  # Return the rasterized PDF content