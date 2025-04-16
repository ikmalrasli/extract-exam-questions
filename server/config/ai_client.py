import os
import asyncio
import json
import time
from typing import List, Tuple
from google import genai
from google.genai import types

class AIClient:
    def __init__(self):
        print("Initializing AI client...")
        self.client = genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY"),
            http_options=types.HttpOptions(timeout=60000)
        )
        self.model = "gemini-2.0-flash"
        self.fixed_content = None

    def _initialize_chat(self):
        """Initialize the fixed prompt content and upload reference files once."""
        upload_time = time.time()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        reference_files = [
            os.path.join(base_dir, "..", "assets", "reference_input_1.pdf"),
            os.path.join(base_dir, "..", "assets", "reference_output_1.txt"),
            os.path.join(base_dir, "..", "assets", "reference_input_2.pdf"),
            os.path.join(base_dir, "..", "assets", "reference_output_2.txt")
        ]
        
        print("Uploading reference files...")
        # Use await here to upload files asynchronously
        self.uploaded_files = [
            self.client.files.upload(file=file_path) for file_path in reference_files
        ]
        upload_duration = time.time() - upload_time
        print(f"Reference files uploaded in {upload_duration:.2f} seconds.")

        self.fixed_content =  [
            # Rules and Schema
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""These are the rules and schema which you will use to extract contents from provided exam question papers (PDF) later:
##GENERAL RULES##
- Avoid null values at ALL COSTS. If you have to use null value, use empty string instead.
- Each main_question, question, and sub-question consists of a number and a content_flow array.
- The JSON output must follow this format:
    - main_questions → Top-level questions numbered \"1.\", \"2.\", \"3.\", etc.
    - questions → Sub-questions numbered \"1(a)\", \"2(b)\", \"3(c)\", etc.
    - sub_questions → Nested sub-questions \"1(a)(i)\", \"2(b)(ii)\", etc.
- OBESERVE CAREFULLY THE NUMBERING IN THE PDF.
- Every main_question must have questions.
- Not every question has sub_questions.
- Extract marks and add its key to their related questions/sub_questions.
- Every main_question, question, sub_question has a content_flow key.
- The content_flow array can contain any of the following in any order, **depending on how they appear in the PDF**:
    - \"text\": Contains question descriptions and instructions (in english and malay, segregated by \"english\" and \"malay\" keys respectively)
    - \"diagram\": Represents figures, charts, or illustrations.
    - \"table\": Represents tabular data extracted from the document.
    - \"row\": A multi-column layout for side-by-side diagrams or elements on the same row.
    - \"answer_space\": Represents the space given for writing down answers.
- Ensure the structure remains hierarchical:
    - Main questions (main_questions) should be nested under the top-level JSON object.
    - Questions (questions) array should be nested under their respective main_questions.
    - Sub-questions (sub_questions) array should be nested under their respective questions if applicable. (For questions that do not have sub_questions, do not add unnecessary sub_questions array)
    - Answer spaces (answer_space) should follow their related questions. **(Do not add answer spaces for Main Questions 9 to 11, this includes their respective nested questions and sub-questions)**
    - Maintain the original order of elements as they appear in the PDF.
- IMPORTANT - Page Break Handling:
    - Merge Across Pages: If a question or sub-question’s text appears to end on one page and continues on the next, combine the text from both pages into one complete content_flow element.
    - Ignore Page Markers: Treat page indicators (such as “page 1”, “page 2”, etc.) as formatting artifacts that should not interrupt the extraction of a single question’s content.
    - Overlapping Extraction: If the content at the end of a page appears incomplete (e.g., it ends in mid-sentence or mid-thought), look to merge it with the beginning of the subsequent page, ensuring that 
    continuation markers like “(i)” for sub-questions are properly attached to the parent question.
- IMPORTANT - Reference Files:
    - Reference input and output files are given later in .pdf and .txt files respectively.
    - Reference outputs are given only for the following:
    ✅ Understanding of JSON hierarchy
    ✅ Recognizing how content_flow elements appear
    ✅ Interpreting marks, diagrams, tables, etc.

    - Reference outputs are NOT to be used for:
    🚫 Generating any question text
    🚫 Reusing sentence structures
    🚫 Copying anything word-for-word

##GENERAL SCHEMA##
Guide to identify main questions:
- numbered \"1\", \"2\", \"3\", etc in **bold** font
- will always be in ascending order, and there will be no skips in the PDF. e.g. (1, 2, 3)
- do not skip any numbers (if you extract 1, 2, 4; you are wrong)
- Numbered \"1\", \"2\", \"3\", etc in the output JSON.
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

##Question schema##
    - Questions are identified with alphabets in the PDF. e.g. (a), (b), (c), etc.
    - will always be in ascending order, and there will be no skips in the PDF. e.g. (a), (b), (c)
    - do not skip any numbers (if you extract (a), (b), (d); you are wrong)
    - Numbered \"1(a)\", \"2(b)\", \"3(c)\", etc in the output JSON.
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

##Sub-Question schema##
    - Sub-Questions are identified with roman numerals in the PDF. e.g. (i), (ii), (iii), etc.
    - will always be in ascending order, and there will be no skips in the PDF. e.g. (i), (ii), (iii)
    - do not skip any numbers (if you extract (i), (ii), (iv); you are wrong)
    - Numbered \"1(a)(i)\", \"2(b)(ii)\", \"3(c)(iii)\", etc in the output JSON.
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

##CONTENT FLOW ELEMENTS##
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
    - **DO NOT EXTRACT TEXT FROM DIAGRAM. Do not create text object from diagram.**
    - To identify diagram, every diagram will have a diagram number right below the diagram. e.g. "Rajah 1/Diagram 1", "Rajah 2", "Diagram 3", etc.
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
    - **DO NOT EXTRACT TEXT FROM TABLE. Do not create text object from table.**
    - To identify table, every table will have a table number right below the table. e.g. "Jadual 1/Table 1", "Jadual 2", "Table 3", etc.
    - Typically has a text object before it that names and describes the table.
- Example JSON object:
```json
{
    \"type\": \"table\",
    \"number\": \"1\",
    \"page\": \"3\"
}
```

- Row
    - A multi-column layout for side-by-side diagrams or elements.
    - To identify row, look for diagrams/tables/text/answer_space that are horizontally aligned (visually).
    - The space between the items can be big or small
    - e.g. in a similar horizontal space, big space in between: "[diagram 1(a)]           [diagram 1(b)]"
    - e.g. in a similar horizontal space, small space in between: "[diagram 1(a)][diagram 1(b)]"
    - For Diagrams and Tables items, DO NOT EXTRACT TEXT FROM THEM. Do not create text object from them.
    - Extract the layout type and the items within the row.
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
    - Extract only what you can see from the PDF. Do not add additional info.
    - Extract the format, number of lines, and options if applicable.
    - **Answer Space DOES NOT apply to Main Questions 9 to 11, including their respective nested questions and sub-questions.**
    - There are three formats: line, multiple-choice, and blank-space.
    a. Line
        - Illustrates the number of dotted-horizontal lines given for writing the answer.
        - To identify line visually, it is usually a long set of dots e.g. "............................"
        - If visually there are two lines of dots e.g. "............................\n............................", then that is 2 lines.
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
    - To identify multiple-choice answer space, visually look for boxes or tables that require the user to ticking them.
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
                    types.Part.from_text(text="""Okay, I understand the rules and schema for extracting content from exam question papers in PDF format. I am ready to process the documents according to the guidelines you've provided. I will pay close attention to the following:

- **JSON Structure:**  Maintaining the correct hierarchical structure with `main_questions`, `questions`, and `sub_questions`.
- **Numbering:**  Following the correct numbering sequence for each question type and avoiding skips.
- **Content Flow:**  Accurately extracting and categorizing content into `text`, `diagram`, `table`, `row`, and `answer_space` elements, including segregating text by language.
- **Page Breaks:**  Handling page breaks by merging content that spans across multiple pages.
- **Marks:**  Associating marks with their respective questions and sub-questions.
- **Answer Spaces:**  Correctly identifying and representing different answer space formats (`line`, `multiple-choice`, `blank-space`) and including options for multiple-choice questions.
- **Ignoring Page Markers:**  Avoiding the inclusion of page numbers or other page-related artifacts in the extracted content.
- **Avoiding Text Extraction from Diagrams and Tables:** Only extracting the diagram/table number and page number.
- **No Answer Spaces for Main Questions 9 to 11:** Excluding answer spaces for main questions 9 to 11 and all their sub-questions.

I will use the provided example JSON snippets as a guide for structuring the output, but I will generate the actual question text, sentence structures, etc., directly from the PDF content.
"""),
                ],
            ),
            # Reference 1
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=self.uploaded_files[0].uri,
                        mime_type=self.uploaded_files[0].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.uploaded_files[1].uri,
                        mime_type=self.uploaded_files[1].mime_type,
                    ),
                    types.Part.from_text(text="""Attached here are the first input (reference_input_1.pdf) and output (reference_output_1.txt) examples that can be used as **reference** when extracting contents from provided PDF later.
**STRICTLY DO NOT COPY CONTENTS FROM THESE REFERENCE FILES GIVEN** when generating JSON output. ONLY study the reference PDF and its output structure.

Reference outputs are given only for the following:
✅ Understanding of JSON hierarchy
✅ Recognizing how content_flow elements appear
✅ Interpreting marks, diagrams, tables, etc.

Reference outputs are NOT to be used for:
🚫 Generating any question text
🚫 Reusing sentence structures
🚫 Copying anything word-for-word"""),
                ],
            ),
            # Reference 2
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=self.uploaded_files[2].uri,
                        mime_type=self.uploaded_files[2].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.uploaded_files[3].uri,
                        mime_type=self.uploaded_files[3].mime_type,
                    ),
                    types.Part.from_text(text="""Attached here are the second input (reference_input_2.pdf) and output (reference_output_2.txt) examples that can be used as reference when extracting contents from provided PDF later.
**STRICTLY DO NOT COPY CONTENTS FROM THESE REFERENCE FILES GIVEN** when generating JSON output. ONLY study the reference PDF and its output structure.

Reference outputs are given only for the following:
✅ Understanding of JSON hierarchy
✅ Recognizing how content_flow elements appear
✅ Interpreting marks, diagrams, tables, etc.

Reference outputs are NOT to be used for:
🚫 Generating any question text
🚫 Reusing sentence structures
🚫 Copying anything word-for-word"""),
                ],
            ),
            # Model Acknowledgment
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""Okay, I have studied the two reference input PDFs (reference_input_1.pdf and reference_input_2.pdf) and their corresponding JSON outputs (reference_output_1.txt and reference_output_2.txt). I now have a better understanding of how to structure the JSON output, especially regarding the nesting of questions and sub-questions, the use of the `content_flow` array, and the handling of different content types like `text`, `diagram`, `table`, `row`, and `answer_space`. I also understand that Main Questions 9-11 DO NOT have Answer Spaces.
I am ready to process new PDF files according to these guidelines.
    """),
                ],
            )
        ]
    
    async def extract_questions(self, pdf: bytes, ranges: List[Tuple[int, int]]) -> List[dict]:
        print("Extracting questions...")

        def build_tasks(indices):
            return [
                self.generate_response(pdf, ranges[i][0], ranges[i][1], i)
                for i in indices
            ]

        max_retries = 2
        total_tasks = len(ranges)
        results = [None] * total_tasks
        pending_indices = list(range(total_tasks))

        for attempt in range(1, max_retries + 1):
            print(f"🔁 Attempt {attempt} for tasks: {pending_indices}")
            tasks = build_tasks(pending_indices)
            attempt_results = await asyncio.gather(*tasks, return_exceptions=True)

            next_pending_indices = []

            for i, res in zip(pending_indices, attempt_results):
                if isinstance(res, Exception):
                    print(f"[❌] Task {i} failed on attempt {attempt}: {res}")
                    next_pending_indices.append(i)
                else:
                    results[i] = res

            if not next_pending_indices:
                break  # all succeeded
            pending_indices = next_pending_indices

        # Now process results
        full_json = {}
        combined_main_questions = []

        for i, result in enumerate(results):
            if isinstance(result, Exception) or result is None:
                print(f"[‼️] Task {i} failed after {max_retries} attempts.")
                continue
            try:
                json_data = json.loads(result)
                combined_main_questions.extend(json_data.get('main_questions', []))
            except json.JSONDecodeError as e:
                print(f"[⚠️] JSON parsing failed for task {i}: {e}")
                print(result)

        full_json['main_questions'] = combined_main_questions
        return full_json


    async def generate_response(self, pdf, start, end, index: int ) -> str:
        start_time = time.perf_counter()
        full_prompt = self.fixed_content.copy()
        full_prompt.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=pdf, mime_type='application/pdf'),
                    types.Part.from_text(text=f"""Extract **Main Questions {start} to {end} ONLY** from this PDF AND ONLY from this PDF. 
**STRICTLY DO NOT COPY CONTENTS FROM REFERENCE FILES GIVEN PREVIOUSLY.**
Keep in mind ALL the rules given previously.""")
                ]
            )
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                top_p=0.9,
                response_mime_type="application/json",
                system_instruction=[
                    types.Part.from_text(text="""You are an AI assistant tasked with extracting structured data from an exam question paper PDF.
Return your output in a clean, hierarchical JSON format that accurately reflects the structure of the questions.
Strictly no null values allowed. 

- Reference input and output files are given later in .pdf and .txt files respectively.
    - Reference outputs are given only for the following:
    ✅ Understanding of JSON hierarchy
    ✅ Recognizing how content_flow elements appear
    ✅ Interpreting marks, diagrams, tables, etc.

    - Reference outputs are NOT to be used for:
    🚫 Generating any question text
    🚫 Reusing sentence structures
    🚫 Copying anything word-for-word"""),
                ],
                # system_instruction=[
                #     types.Part.from_text(text="""You are an AI assistant tasked with extracting structured data from an exam question paper PDF.
                #                             Return your output in a clean, hierarchical JSON format that accurately reflects the structure of the questions.
                #                             Strictly no null values allowed. STRICTLY DO NOT COPY FROM THE REFERENCES GIVEN."""),
                # ],
            )
        )
        
        elapsed = time.perf_counter() - start_time
        print(f"⏱️ Prompt {index + 1} took {elapsed:.2f} seconds")
        
        return response.text