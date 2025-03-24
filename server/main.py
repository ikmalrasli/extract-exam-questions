import json
from datetime import datetime
from dotenv import load_dotenv
import time  # Add this import at the top of the file

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from modules.sections import identify_sections
from modules.questions import build_extract_section_data_prompt, validate_section_content
from modules.sections import build_identify_sections_prompt, identify_sections
from modules.new import newPrompt, newPrompt2
from modules.utils import get_reference_pdf, get_rasterized_pdf

from config.logger import log_error
from config.ai_client import get_ai_response, convert_pdf_to_part

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
        pdf = convert_pdf_to_part(user_pdf_content)
        
        unique_id = datetime.now().strftime("%Y%m%d%H%M%S") + '_' + pdf_file.filename.lower().replace(" ", "_")
        supabase.storage.from_("files").upload(unique_id, user_pdf_content)
        download_link = supabase.storage.from_("files").get_public_url(unique_id)

        # insert document and get the inserted record's ID
        insert_response = supabase.table("documents").insert({"file_name": pdf_file.filename, "file_url": download_link}).execute()
        document_id = insert_response.data[0]['id']

        # return extract_data(pdf, document_id)
        background_tasks.add_task(extract_data, pdf, document_id)
        return {
            "status": "success", 
            "message": "File uploaded successfully. Please wait while it being processed.", 
            "data": { "document_id": document_id, "file_url": download_link }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e), "data": None})

def extract_data(pdf, document_id: str):
    start_time = time.time()  # Capture the start time
    full_json = []
    combined_main_questions = []  # Initialize a list to hold combined questions

    # Loop from 1 to 11
    for i in range(1, 12):  # This will loop through numbers 1 to 11
        attempts = 0
        max_attempts = 3
        success = False
        
        while attempts < max_attempts and not success:
            attempts += 1
            print(f"Attempt {attempts}: Extracting questions for {i}")
            prompt = newPrompt(i)
            try:
                response = get_ai_response([pdf, prompt])
                response_json = json.loads(response.text)
                
                # Combine the main_q from the response into combined_main_q
                if "main_questions" in response_json:
                    combined_main_questions.extend(response_json["main_questions"])
                
                print(f"Questions extracted successfully for {i}")
                success = True
            except Exception as e:
                print(f"Error extracting questions for {i} (Attempt {attempts}): {str(e)}")
                if attempts == max_attempts:
                    print(f"Failed to extract questions for {i} after {max_attempts} attempts")
                    raise HTTPException(status_code=500, 
                        detail=f"Failed to extract questions for range {i} after {max_attempts} attempts")
    
    # After all attempts, append the combined main_q to full_json
    full_json.append({"main_questions": combined_main_questions})
    
    
    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate elapsed time
    supabase.table("documents").update({"data": full_json, "status": "extracted"}).eq("id", document_id).execute()
    return {
        "status": "success",
        "message": "Questions extracted successfully",
        "data": full_json,
        "elapsed_time": elapsed_time  # Include elapsed time in the response
    }

def extract_data2(pdf):
    start_time = time.time()  # Capture the start time
    full_json = []
    combined_main_questions = []  # Initialize a list to hold combined questions

    ranges = [(1, 3), (4, 6), (7, 8), (9, 10), (11, 11)]
    for start, end in ranges:
        attempts = 0
        max_attempts = 3
        success = False
        
        while attempts < max_attempts and not success:
            attempts += 1
            print(f"Attempt {attempts}: Extracting questions for {start} to {end}")
            prompt = newPrompt2(start, end)
            try:
                response = get_ai_response([pdf, prompt])
                response_json = json.loads(response.text)
                
                # Combine the main_q from the response into combined_main_q
                if "main_questions" in response_json:
                    combined_main_questions.extend(response_json["main_questions"])
                
                print(f"Questions extracted successfully for {start} to {end}")
                success = True
            except Exception as e:
                print(f"Error extracting questions for {start} to {end} (Attempt {attempts}): {str(e)}")
                if attempts == max_attempts:
                    print(f"Failed to extract questions for {start} to {end} after {max_attempts} attempts")
                    # supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
                    raise HTTPException(status_code=500, 
                        detail=f"Failed to extract questions for range {start}-{end} after {max_attempts} attempts")
    
    # After all attempts, append the combined main_q to full_json
    full_json.append({"main_questions": combined_main_questions})
    
    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate elapsed time

    return {
        "status": "success",
        "message": "Questions extracted successfully",
        "data": full_json,
        "elapsed_time": elapsed_time  # Include elapsed time in the response
    }


# def extract_data(pdf, sections, document_id: str):
#     reference_pdf_content = get_reference_pdf()
#     reference_pdf = convert_pdf_to_part(reference_pdf_content)

#     print("Extracting data from sections...")
#     sections_data = []
#     for section in sections:
#         print(f"Processing section: {section['name']}")
#         prompt = build_extract_section_data_prompt(section)
#         try:
#             response = get_ai_response([reference_pdf, pdf, prompt])
#             validate_section_content(response.text, section['name'])
#             print(response.text)
#             response_json = json.loads(response.text)
#             sections_data.append(response_json)
#         except Exception as e:
#             print(f"Error in extract_section_data: {str(e)}")
#             supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
#             log_error(str(e), response.text if 'response' in locals() else None)
#             raise ValueError(f"Error extracting section data: {str(e)}")
    
#     supabase.table("documents").update({"data": sections_data, "status": "extracted"}).eq("id", document_id).execute()

#     with open("outputs/temporary_output_data.json", "w", encoding="utf-8") as json_file:
#         json.dump(sections_data, json_file, ensure_ascii=False, indent=4)
#     return {"status": "Success", "data": sections_data}
