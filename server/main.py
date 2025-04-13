import json
import re
import os
from datetime import datetime
from dotenv import load_dotenv
import time
import cv2

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from modules.new import newPrompt, newPrompt2
from modules.utils import get_reference_pdf, get_rasterized_pdf
from modules.wordgen import generate
from modules.crop_img import get_images, update_json_with_url

# from config.ai_client import get_ai_response
from config.ai_client import AIClient

from db.init import init_db

load_dotenv()

app = FastAPI()
supabase = init_db()

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/documents")
def get_documents():
    response = supabase.table("documents").select("*").order("uploaded_date", desc=True).execute()
    return {
        "status": "success",
        "message": "Documents fetched successfully",
        "data": {
            "documents": response.data
        }
    }

@app.get("/documents/{id}")
def get_document_by_id(id: str):
    response = supabase.table("documents").select("*").eq("id", id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "status": "success",
        "message": "Document fetched successfully",
        "data": response.data[0]
    }

@app.delete("/documents/{id}")
def delete_document(id: str = Path(...)):
    response = supabase.table("documents").delete().eq("id", id).execute()
    if response.status_code == 204:  # No content means successful deletion
        return {
            "status": "success",
            "message": "Document deleted successfully."
        }
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@app.post("/extract_questions")
async def analyse_pdf(background_tasks: BackgroundTasks, pdf_file: UploadFile = File(...)):
    try:
        if not pdf_file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Input PDF file must end with .pdf")

        user_pdf_content = await pdf_file.read()
        # rasterized_pdf = get_rasterized_pdf(user_pdf_content)
        # pdf = convert_pdf_to_part(user_pdf_content)
    
        # return extract_data2(user_pdf_content)
    
        unique_id = datetime.now().strftime("%Y%m%d%H%M%S") + '_' + pdf_file.filename.lower().replace(" ", "_")
        supabase.storage.from_("files").upload(unique_id, user_pdf_content)
        download_link = supabase.storage.from_("files").get_public_url(unique_id)

        # insert document and get the inserted record's ID
        insert_response = supabase.table("documents").insert({"file_name": pdf_file.filename, "file_url": download_link}).execute()
        document_id = insert_response.data[0]['id']

        background_tasks.add_task(extract_data, user_pdf_content, document_id)
        return {
            "status": "success", 
            "message": "File uploaded successfully. Please wait while it being processed.", 
            "data": { "document_id": document_id, "file_url": download_link }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e), "data": None})

async def extract_data(pdf, document_id):
    start_time = time.time()  # Capture the start time
    ai_client = AIClient(pdf)
    
    # Initialize the chat asynchronously
    ai_client._initialize_chat(pdf)  # Make sure to await this
    
    ranges = [(1, 4), (5, 8), (9, 11)]

    try:
        # Await the extraction of questions asynchronously
        full_json = await ai_client.extract_questions(ranges)
        
        # Update the document with the extracted data
        supabase.table("documents").update({"data": full_json, "status": "extracted"}).eq("id", document_id).execute()
        end_time = time.time()  # Capture the end time
        elapsed_time = end_time - start_time  # Calculate elapsed time
        print(f"Total elapsed time (with file upload): {elapsed_time:.2f} seconds")
        
        return {
            "status": "success",
            "message": "Questions extracted successfully",
            "elapsed_time": elapsed_time,
            "data": full_json
        }
    except Exception as e:
        print(f"Error extracting questions: {str(e)}")
        supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/generate_word")
async def generate_word(request: Request):
    data = await request.json()
    
    json_data = data.get('jsonData')  # Access jsonData
    filename = data.get('filename')  # Access filename

    document_path = generate(json_data)  # Call generate and get the document path
    
    return FileResponse(document_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=filename)
