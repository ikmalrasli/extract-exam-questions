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

from config.ai_client import get_ai_response

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

def extract_data(pdf, document_id):
    start_time = time.time()  # Capture the start time
    full_json = {}
    combined_main_questions = []  # Initialize a list to hold combined questions

    ranges = [(1, 4), (5, 8), (9, 11)]
    for start, end in ranges:
        attempts = 0
        max_attempts = 5
        success = False
        
        while attempts < max_attempts and not success:
            attempts += 1
            print(f"Attempt {attempts}: Extracting questions for {start} to {end}")
            
            try:
                response = get_ai_response(pdf, start, end)
                response_json = json.loads(response.text)
                
                if "main_questions" in response_json:
                    combined_main_questions.extend(response_json["main_questions"])
                
                print(f"Questions extracted successfully for {start} to {end}")
                success = True
            except Exception as e:
                print(f"Error extracting questions for {start} to {end} (Attempt {attempts}): {str(e)}")
                if attempts == max_attempts:
                    print(f"Failed to extract questions for {start} to {end} after {max_attempts} attempts")
                    print(response.text)
                    supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
                    raise HTTPException(status_code=500, 
                        detail=f"Failed to extract questions for range {start}-{end} after {max_attempts} attempts")
    
    full_json["main_questions"] = combined_main_questions

    # Call the cropping function and get cropped images
    cropped_images = get_images(pdf, full_json)

    for cropped_image, expected_num, expected_type, page_num in cropped_images:
        # Validate image
        if cropped_image is None or cropped_image.size == 0:
            print(f"Invalid image data for page {page_num} - skipping")
            continue
        
        try:
            h, w = cropped_image.shape[:2]
            if h == 0 or w == 0:
                print(f"Empty image dimensions for page {page_num} - skipping")
                continue
        except Exception as e:
            print(f"Invalid image format for page {page_num}: {str(e)} - skipping")
            continue

        # Encode image
        success, buffer = cv2.imencode('.jpg', cropped_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not success or buffer.size == 0:
            print(f"Failed to encode image for page {page_num} - skipping")
            continue

        # Create safe filename
        file_name = f"page_{page_num}_{expected_type}_{expected_num}.jpg"
        file_name = re.sub(r'[^\w\-_. ]', '_', file_name)
        
        # Save image
        try:
            supabase.storage.from_("img").upload(f"{document_id}/{file_name}", buffer.tobytes())
            file_url = supabase.storage.from_("img").get_public_url(f"{document_id}/{file_name}")
            update_json_with_url(full_json, page_num, expected_type, expected_num, file_url)
            
            print(f"Successfully uploaded image. URL: {file_url}")
        except Exception as e:
            print(f"Failed to upload image {file_name}: {str(e)}")
            continue
            
        

    supabase.table("documents").update({"data": full_json, "status": "extracted"}).eq("id", document_id).execute()
    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print(f"Total elapsed time: {elapsed_time} seconds")
    return {
        "status": "success",
        "message": "Questions extracted successfully",
        "elapsed_time": elapsed_time,
        "data": full_json
    }

def extract_data2(pdf):
    start_time = time.time()  # Capture the start time
    full_json = {}
    combined_main_questions = []  # Initialize a list to hold combined questions

    ranges = [(1, 4), (5, 8), (9, 11)]
    for start, end in ranges:
        attempts = 0
        max_attempts = 5
        success = False
        
        while attempts < max_attempts and not success:
            attempts += 1
            print(f"Attempt {attempts}: Extracting questions for {start} to {end}")
            
            try:
                response = get_ai_response(pdf, start, end)
                response_json = json.loads(response.text)
                
                # Combine the main_questions from the response into combined_main_questions
                if "main_questions" in response_json:
                    combined_main_questions.extend(response_json["main_questions"])
                
                print(f"Questions extracted successfully for {start} to {end}")
                success = True
            except Exception as e:
                print(f"Error extracting questions for {start} to {end} (Attempt {attempts}): {str(e)}")
                if attempts == max_attempts:
                    print(f"Failed to extract questions for {start} to {end} after {max_attempts} attempts")
                    print(response.text)
                    raise HTTPException(status_code=500, 
                        detail=f"Failed to extract questions for range {start}-{end} after {max_attempts} attempts")
    
    # After all attempts, append the combined main_q to full_json
    full_json["main_questions"] = combined_main_questions
    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print(f"Total elapsed time: {elapsed_time} seconds")
    return {
        "status": "success",
        "message": "Questions extracted successfully",
        "elapsed_time": elapsed_time,
        "data": full_json
    }
    
@app.post("/generate_word")
async def generate_word(request: Request):
    data = await request.json()
    
    json_data = data.get('jsonData')  # Access jsonData
    filename = data.get('filename')  # Access filename

    document_path = generate(json_data)  # Call generate and get the document path
    
    return FileResponse(document_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=filename)
