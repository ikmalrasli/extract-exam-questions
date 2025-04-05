import os
import json
import base64
import time
from typing import List, Tuple
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        logger.info("Initializing AI client...")
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = "gemini-2.0-flash"
        self.chat_history = []
        self.uploaded_files = []
        self._initialize_chat_history()

    def _initialize_chat_history(self):
        """Initialize the fixed prompt content and upload reference files once"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        reference_files = [
            os.path.join(base_dir, "..", "assets", "reference_input_1.pdf"),
            os.path.join(base_dir, "..", "assets", "reference_output_1.txt"),
            os.path.join(base_dir, "..", "assets", "reference_input_2.pdf"),
            os.path.join(base_dir, "..", "assets", "reference_output_2.txt")
        ]
        
        print("Uploading reference files...")
        self.uploaded_files = [self.client.files.upload(file=file_path) for file_path in reference_files]

        print("Reference files uploaded successfully.")
        self.chat_history = [
            # Rules and Schema
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""These are the rules and schema which you will use to extract contents from provided exam question papers (PDF) later:
    **GENERAL RULES**
    - Avoid null values at ALL COSTS.
    - Each main_question, question, and sub-question consists of a number and a content_flow array.
    - The JSON output must follow this format:
        - main_questions → Top-level questions numbered \"1\", \"2\", \"3\", etc.
        - questions → Sub-questions numbered \"1(a)\", \"2(b)\", \"3(c)\", etc.
        - sub_questions → Nested sub-questions numbered \"1(a)(i)\", \"2(b)(ii)\", etc.
    - Every main_question must have questions.
    - Not every question has sub_questions.
    - Extract marks and add its key to their related questions/sub_questions.
    - Every main_question, question, sub_question has a content_flow key.
    - The content_flow array can contain any of the following in any order, **depending on how they appear in the PDF**:
        - \"text\": Contains question descriptions and instructions (in english and malay, segregated by \"english\" and \"malay\" keys respectively)
        - \"diagram\": Represents figures, charts, or illustrations.
        - \"table\": Represents tabular data extracted from the document.
        - \"row\": A multi-column layout for side-by-side diagrams, tables, text, answer spaces on the same row (same y-coordinates).
        - \"answer_space\": Represents the space given for writing down answers.
    - Ensure the structure remains hierarchical:
        - Main questions (main_questions) should be nested under the top-level JSON object.
        - Questions (questions) array should be nested under their respective main_questions.
        - Sub-questions (sub_questions) array should be nested under their respective questions if applicable. (For questions that do not have sub_questions, do not add unnecessary sub_questions array)
        - Answer spaces (answer_space) should follow their related questions. **(Do not add answer spaces for Main Questions 9 to 11, this includes their respective nested questions and sub-questions)**
        - Maintain the original order of elements as they appear in the PDF.

    **GENERAL SCHEMA**
    Guide to identify main questions:
    - numbered \"1\", \"2\", \"3\", etc in **bold** font
    ```json
    {
        \"main_questions\": [
            {
                \"number\": \"<1 | 2 | 3 | etc.>\",
                \"content_flow\": [
                    {
                        \"type\": \"text\",
                        \"text\": {
                            \"malay\": \"<Text in Malay>\",
                            \"english\": \"<Text in English>\"
                        }
                    },
                    {
                        \"type\": \"diagram\",
                        \"number\": \"<1 | 1.1 | 1.2 | 2 | etc.>\",
                        \"page\": \"<Page Number>\"
                    },
                    {
                        \"type\": \"row\",
                        \"items\": [
                            {
                                \"type\": \"diagram\",
                                \"number\": \"<1 | 1.1 | 1.2 | 2 | etc.>\",
                                \"page\": \"<Page Number A>\"
                            },
                            {
                                \"type\": \"diagram\",
                                \"number\": \"<1 | 1.1 | 1.2 | 2 | etc.>\",
                                \"page\": \"<Page Number B>\"
                            },
                        ]
                    },
                    {
                        \"type\": \"table\",
                        \"number\": \"<Table Number>\",
                        \"page\": \"<Page Number>\"
                    },
                ],
                \"questions\": [
                    {
                        \"number\": \"<1(a) | 1(b) | 2(a) | etc.>\",
                        \"marks\": \"<1 | 2 | 3 | etc.>\",
                        \"content_flow\": [
                            {
                                \"type\": \"text\",
                                \"text\": {
                                    \"malay\": \"<Text in Malay>\",
                                    \"english\": \"<Text in English>\"
                                }
                            },
                            {
                                \"type\": \"answer_space\",
                                \"format\": \"<multiple-choice | line | blank-space>\",
                                \"lines\": \"<Number of Lines>\",
                                \"options\": [
                                    {
                                        \"malay\": \"<Option in Malay>\",
                                        \"english\": \"<Option in English>\"
                                    }
                                ]
                            },
                        ],
                        \"sub_questions\": [
                            {
                                \"number\": \"<1(a)(i) | 1(b)(ii) | 2(c)(i) | etc.>\",
                                \"marks\": \"<1 | 2 | 3 | etc.>\",
                                \"content_flow\": [
                                    {
                                        \"type\": \"text\",
                                        \"text\": {
                                            \"malay\": \"<Text in Malay>\",
                                            \"english\": \"<Text in English>\"
                                        }
                                    },
                                    {
                                        \"type\": \"answer_space\",
                                        \"format\": \"<multiple-choice | line | blank-space>\",
                                        \"lines\": \"<Number of Lines>\"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    ```

    **Question schema**
        - Numbered \"1(a)\", \"2(b)\", \"3(c)\", etc.
        - Example JSON object inside a main_question's \"questions\" array:
    ```json
    \"main_questions\": [
        {
            \"number\": \"1\",
            \"content_flow\": [
            ],
            \"questions\": [
                {
                    \"number\": \"1(a)\",
                    \"marks\": \"1\",
                    \"content_flow\": [
                        {
                            \"type\": \"text\",
                            \"text\": {
                                \"malay\": \"Nyatakan Prinsip Keabadian Momentum?\",
                                \"english\": \"State the Principle of Conservation of Momentum?\"
                            }
                        }
                    ]
                },
                {
                    \"number\": \"1(b)\",
                    \"marks\": \"1\",
                    \"content_flow\": [
                        {
                            \"type\": \"text\",
                            \"text\": {
                                \"malay\": \"Nyatakan jenis perlanggaran yang terlibat dalam Rajah 1.\",
                                \"english\": \"State the type of collision involved in Diagram 1.\"
                            }
                        }
                    ]
                }
            ]
        }
    ]
    ```

    **Sub-Question schema**
        - Numbered \"1(a)(i)\", \"2(b)(ii)\", \"3(c)(iii)\", etc.
        - Example JSON object inside a question's \"content_flow\" array:
    ```json
    \"questions\": [
        {
        \"number\": \"1(a)\",
        \"content_flow\": [
            ],
            \"sub_questions\": [
                {
                    \"number\": \"1(a)(i)\",
                    \"marks\": \"1\",
                    \"content_flow\": [
                        {
                            \"type\": \"text\",
                            \"text\": {
                                \"malay\": \"Lakarkan pesongan alur elektron dalam Rajah 1, jika nilai voltan lampau tinggi ( V.L.T ) ditingkatkan kepada 5000 V?\",
                                \"english\": \"Sketch the electron flow deflection in Diagram 1, if the value of the extra high tension ( EHT ) is increased to 5000 V?\"
                            }
                        }
                    ]
                },
                {
                    \"number\": \"1(a)(ii)\",
                    \"marks\": \"1\",
                    \"content_flow\": [
                        {
                            \"type\": \"text\",
                            \"text\": {
                                \"malay\": \"Beri satu sebab bagi jawapan anda di 1(c)(i).\",
                                \"english\": \"Give one reason for your answer in 1(c)(i).\"
                            }
                        }
                    ]
                },
            ]
        }
    ]
    ```

    **CONTENT FLOW ELEMENTS**
    - **Text**
        - Extract text and segregate into malay and english keys.
        - If there is a new line but within the same language, add a \\n
        - Example JSON object:
    ```json
    {
        \"type\": \"text\",
        \"text\": {
            \"malay\": \"Apakah kesan negatif penggunaan tenaga hidroelektrik?\\nBerikan sebab\",
            \"english\": \"What are the negative impacts of using hydroelectric energy?\\nGive reasons.\"
        }
    }
    ```

    - **Diagram**
        - Represents figures, charts, or illustrations.
        - Only extract the diagram number and its PDF page number of appearance.
        - Will have a diagram number right below the diagram.
        - Typically has a text object before it that names and describes the diagram.
    - Example JSON object:
    ```json
    {
        \"type\": \"diagram\",
        \"number\": \"2.1\",
        \"page\": \"5\"
    }
    ```

    - **Table**
        - Represents tabular data extracted from the document.
        - Only extract the table number and its PDF page number of appearance.
        - Will have a table number right below the table.
        - Typically has a text object before it that names and describes the table.
    - Example JSON object:
    ```json
    {
        \"type\": \"table\",
        \"number\": \"1\",
        \"page\": \"3\"
    }
    ```

    - **Row**
        - A multi-column layout for side-by-side diagrams, tables, text, answer spaces on the same row.
        - Extract the layout type and the items within the row.
        - The items listed must be same or similar y-coordinates to be considered within the same row.
        - Example 1 JSON object:
    ```json
    {
        \"type\": \"row\",
        \"items\": [
            {
                \"type\": \"diagram\",
                \"number\": \"1.1\",
                \"page\": \"2\"
            },
            {
                \"type\": \"diagram\",
                \"number\": \"1.2\",
                \"page\": \"2\"
            }
        ]
    }
    ```

        - Example 2 JSON object:
    ```json
    {
        \"type\": \"row\",
        \"items\": [
            {
                \"type\": \"text\",
                \"text\": {
                    \"malay\": \"Zarah alfa:\",
                    \"english\": \"Alpha particle:\"
                }
            },
            {
                \"type\": \"answer_space\",
                \"format\": \"line\",
                \"lines\": 1
            },
            {
                \"type\": \"text\",
                \"text\": {
                    \"malay\": \"Zarah beta:\",
                    \"english\": \"Beta particle:\"
                }
            },
            {
                \"type\": \"answer_space\",
                \"format\": \"line\",
                \"lines\": 1
            }
        ]
    }
    ```

    - **Answer Space**
        - Represents the space given for writing down answers.
        - Extract the format, number of lines, and options if applicable.
        - **Answer Space DOES NOT apply to Main Questions 9 to 11, including their respective nested questions and sub-questions.**
        - There are three formats: line, multiple-choice, and blank-space.
        a. Line
            - Illustrates the number of dotted-horizontal lines given for writing the answer.
            - Add a \"line\" key to the answer_space type element for line formats to represent the number of lines.
            - Example JSON object:
        ```json
        {
            \"type\": \"answer_space\",
            \"format\": \"line\",
            \"lines\": <Number of lines>
        }
        ```

        b. Blank Space
            - Represents a blank space for answers.
            - A blank space is determined by visually identifying the space given from the question text and the marks allocator.
            - Typically for questions that involve calculations.
            - Example JSON object:
        ```json
        {
            \"type\": \"answer_space\",
            \"format\": \"blank-space\"
        }
        ```

        c. Multiple-Choice
        - Represents a multiple-choice question that requires the user to select/tick the correct answer from a set of predetermined options.
        - Add an \"options\" key to represent the predetermined options.
        - Extract the options in both Malay and English.
        - Example JSON object:
        ```json
        {
            \"type\": \"answer_space\",
            \"format\": \"multiple-choice\",
            \"options\": [
                {
                    \"malay\": \"spektrum garis\",
                    \"english\": \"line spectrum\"
                },
                {
                    \"malay\": \"spektrum selanjar\",
                    \"english\": \"continuous spectrum\"
                }
            ]
        }
        ```"""),
                ],
            ),
            # Model Acknowledgement
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""Okay, I understand the rules and schema. I am ready to process the exam question papers and extract the content into the specified JSON format. I will pay close attention to:

    -   Maintaining the correct hierarchical structure.
    -   Accurately identifying and categorizing content flow elements (text, diagram, table, row, answer\\_space).
    -   Handling Malay and English text appropriately.
    -   Extracting marks for questions and sub-questions.
    -   Avoiding null values.
    -   Excluding answer spaces for Main Questions 9 to 11 and their nested questions/sub-questions.
    -   Including diagram, table numbers and their page number.
    -   Following the numbering convention for main questions, questions, and sub-questions.
    """),
                ],
            ),
            # Example references 1
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(file_uri=self.uploaded_files[0].uri, mime_type=self.uploaded_files[0].mime_type),
                    types.Part.from_uri(file_uri=self.uploaded_files[1].uri, mime_type=self.uploaded_files[1].mime_type),
                    types.Part.from_text(text="""Attached here are the first input and output examples that can be used as **reference** when extracting contents from provided PDF later.
Do not copy exactly from these references when generating JSON output, ONLY study the reference PDF and the output structure.""")
                ]
            ),
            # Model Acknowledgement
            types.Content(
                role="model",
                parts=[
                types.Part.from_text(text="""Okay, I have analyzed the provided reference output and I have a clear understanding of the expected JSON structure, the different content\\_flow types, and the overall extraction logic. I will use this understanding to process future exam papers and generate accurate JSON outputs.
"""),
                ],
            ),
            # Example references 2
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(file_uri=self.uploaded_files[2].uri, mime_type=self.uploaded_files[2].mime_type),
                    types.Part.from_uri(file_uri=self.uploaded_files[3].uri, mime_type=self.uploaded_files[3].mime_type),
                    types.Part.from_text(text="""Attached here are the second input and output examples that can be used as reference when extracting contents from provided PDF later.
Do not copy exactly from these references when generating JSON output, ONLY study the reference PDF and the output structure.""")
                ]
            ),
            # Model Acknowledgement
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""Understood. I have carefully studied the second reference input and output. I'm now well-equipped with different scenarios and ready to work on the actual PDF content.
    """),
                ],
            )
        ]
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )

    def _process_single_range(self, pdf_bytes: bytes, start: int, end: int) -> dict:
        """Process a single question range with automatic retries"""
        start_time = time.time()
        logger.info(f"Processing range {start}-{end}")
        current_message = self.chat_history.copy()
        current_message.extend([
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                    types.Part.from_text(text=f"Extract Main Questions {start} to {end}")
                ]
            )
        ])

        response = self.client.models.generate_content(
            model=self.model,
            contents=current_message,
            config=types.GenerateContentConfig(
                temperature=0.2,
                top_p=0.9,
                response_mime_type="application/json"
            )
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"API usage for range {start}-{end}: {response.usage_metadata}")
        logger.info(f"Total elapsed time for range {start}-{end}: {elapsed_time} seconds")
        
        response_json = json.loads(response.text)
        
        if "main_questions" not in response_json:
            raise ValueError("Response missing 'main_questions' key")
            
        return response_json
    
    def extract_questions(self, pdf_bytes: bytes, ranges: List[Tuple[int, int]]) -> List[dict]:
        """Process multiple question ranges with comprehensive error handling"""
        results = []
        total_attempts = 0
        
        for start, end in ranges:
            range_success = False
            last_exception = None
            
            for attempt in range(1, 6):  # Maximum 5 attempts per range
                total_attempts += 1
                try:
                    logger.info(f"Attempt {attempt} for range {start}-{end}")
                    response = self._process_single_range(pdf_bytes, start, end)
                    results.extend(response["main_questions"])
                    range_success = True
                    break
                except Exception as e:
                    last_exception = e
                    wait_time = min(2 ** attempt, 30)  # Cap at 30 seconds
                    logger.warning(
                        f"Attempt {attempt} failed for range {start}-{end}. "
                        f"Waiting {wait_time}s before retry. Error: {str(e)}"
                    )
                    time.sleep(wait_time)
            
            if not range_success and last_exception:
                logger.error(
                    f"Failed to process range {start}-{end} after 5 attempts. "
                    f"Last error: {str(last_exception)}"
                )
                raise RuntimeError(
                    f"Failed to extract questions {start}-{end} after 5 attempts. "
                    f"Original error: {str(last_exception)}"
                ) from last_exception
        
        logger.info(
            f"Completed processing all ranges. Total attempts: {total_attempts}. "
            f"Successfully extracted {len(results)} questions."
        )
        return results

    @staticmethod
    def convert_pdf_to_part(pdf_bytes: bytes):
        """Utility method for PDF conversion"""
        return {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("utf-8")}