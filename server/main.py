import json
from datetime import datetime
from dotenv import load_dotenv
import time

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from modules.new import newPrompt, newPrompt2
from modules.utils import get_reference_pdf, get_rasterized_pdf

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
    full_json = []
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
                    supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
                    raise HTTPException(status_code=500, 
                        detail=f"Failed to extract questions for range {start}-{end} after {max_attempts} attempts")
    
    # After all attempts, append the combined main_q to full_json
    full_json.append({"main_questions": combined_main_questions})
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
    full_json = []
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
    full_json.append({"main_questions": combined_main_questions})
    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print(f"Total elapsed time: {elapsed_time} seconds")
    return {
        "status": "success",
        "message": "Questions extracted successfully",
        "elapsed_time": elapsed_time,
        "data": full_json
    }