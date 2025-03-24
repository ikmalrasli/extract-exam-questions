from google import genai
import os
import base64
import google.generativeai as genai

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

def configure_model():
  genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
  return genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction="You are an Exam Paper Structure Extractor. Your task is to create a VALID JSON object from the PDF content. STRICTLY NO NULL VALUES ARE ALLOWED."
  )

def get_ai_response(contents, response_schema=None, model="gemini-2.0-flash"):
  model = configure_model()
  response = model.generate_content(contents)
  print(response.usage_metadata)
  return response

def convert_pdf_to_part(pdf_file):
  pdf_content_base64 = base64.b64encode(pdf_file).decode("utf-8")
  return {"mime_type": "application/pdf", "data": pdf_content_base64}


# Gemini 2.0 Configurations here:

# client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# def get_ai_response(contents, response_schema=None, model="gemini-1.5-flash"):
#   response = client.models.generate_content(
#     model=model,
#     contents=contents,
#     config={
#         "response_mime_type": "application/json",
#         **({"response_schema": response_schema} if response_schema is not None else {})
#     }
#   )
#   return response

# def convert_pdf_to_part(pdf_file):
#   pdf_content_base64 = base64.b64encode(pdf_file).decode("utf-8")
#   return genai.types.Part.from_bytes(data=pdf_content_base64, mime_type="application/pdf")