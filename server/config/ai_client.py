import os
import base64
from google import genai
from google.genai import types

def get_ai_response(file, start, end):
  client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
  
  model = "gemini-2.0-flash"
  
  base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
  reference_input_file_path = os.path.join(base_dir, "..", "reference_files", "reference_input.pdf")
  reference_output_file_path = os.path.join(base_dir, "..", "reference_files", "reference_output.txt")
  files = [
    # Make the reference input file available in local system working directory
    client.files.upload(file=reference_input_file_path),
    # Make the reference output file available in local system working directory
    client.files.upload(file=reference_output_file_path)
  ]
  
  fixed_contents = [
        # Rules and Schema
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""These are the rules and schema which you will use to extract contents from provided exam question papers (PDF) later:
**GENERAL RULES**
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
     - \"text\": Contains question descriptions and instructions (in english and malay, segregated by "english" and "malay" keys respectively)
     - \"diagram\": Represents figures, charts, or illustrations.
     - \"table\": Represents tabular data extracted from the document.
     - \"row\": A multi-column layout for side-by-side diagrams or elements.
     - \"question\": Marks a question reference. (Only for content_flow array under main_question, *will be multiple according to PDF*)
     - \"sub_question\": Marks a sub_question reference. (Only for content_flow array under question, *will be multiple according to PDF*)
     - "answer_space": Represents the space given for writing down answers.
- Ensure the structure remains hierarchical:
     - Main questions (main_questions) should be nested under the top-level JSON object.
     - Questions (questions) array should be nested under their respective main_questions.
     - Sub-questions (sub_questions) array should be nested under their respective questions if applicable. (For questions that do not have sub_questions, do not add unnecessary sub_questions array)
     - Answer spaces (answer_space) should follow their related questions. **(Do not add answer spaces for Main Questions 9 to 11, this includes their respective nested questions and sub-questions)**
     - Maintain the original order of elements as they appear in the PDF.

**GENERAL SCHEMA**
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
                    \"columns\": <Number of Columns>,
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
                {
                    \"type\": \"questions\"
                }
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
                        {
                            \"type\": \"sub_questions\"
                        }
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

**CONTENT FLOW ELEMENTS**
- **Text**
    - Extract text and segregate into malay and english keys.
    - If there is a new line but within the same language, add a \\\\n
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

- Row
    - A multi-column layout for side-by-side diagrams or elements.
    - Extract the layout type and the items within the row.
    - Number of columns MUST match the number of items.
    - Example 1 JSON object:
```json
{
    \"type\": \"row\",
    \"columns\": 2,
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
    \"columns\": 4,
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

- **Question**
    - Marks a question reference inside a main_question's \"content_flow\" array.
    - Numbered \"1(a)\", \"2(b)\", \"3(c)\", etc.
    - Example JSON object inside a main_question's \"content_flow\" and \"questions\" array:
```json
\"main_questions\": [
    {
        \"number\": \"1\",
        \"content_flow\": [
            {
                \"type\": \"questions\"
            }
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

- **Sub-Question**
    - Marks a sub_question reference inside a question's \"content_flow\" array.
    - Numbered \"1(a)(i)\", \"2(b)(ii)\", \"3(c)(iii)\", etc.
    - Example JSON object inside a question's \"content_flow\" and \"sub_questions\" array:
```json
\"questions\": [
    {
      \"number\": \"1(a)\",
      \"content_flow\": [
            {
                \"type\": \"sub_questions\"
            }
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

- **Answer Space**
    - Represents the space given for writing down answers.
    - Extract the format, number of lines, and options if applicable.
    - **Answer Space DOES NOT apply to Main Questions 9 to 11, including their respective nested questions and sub-questions.**
    - There are three formats: line, multiple-choice, and blank-space.
    a. Line
        - Illustrates the number of dotted-horizontal lines given for writing the answer.
        - Add a "line" key to the answer_space type element for line formats to represent the number of lines.
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
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""Okay, I understand the rules and schema for extracting content from exam question papers in PDF format. I am ready to process the provided PDF content and generate a JSON output that adheres to the specified structure and guidelines. I will pay close attention to:

-   Maintaining the hierarchical structure of main questions, questions, and sub-questions.
-   Accurately extracting and segregating text into Malay and English.
-   Identifying and representing diagrams, tables, and rows with their corresponding numbers and page numbers.
-   Correctly identifying and representing different answer space formats (line, multiple-choice, and blank-space) with the appropriate attributes.
-   Maintaining the order of elements as they appear in the PDF.
-   Including question marks where applicable.
-   Omitting answer spaces for Main Questions 9 to 11.

I will await the PDF content to begin the extraction process.
"""),
            ],
        ),
        # Reference examples
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri,
                    mime_type=files[0].mime_type,
                ),
                types.Part.from_uri(
                    file_uri=files[1].uri,
                    mime_type=files[1].mime_type,
                ),
                types.Part.from_text(text="""Attached are the example input and output that can be used as **reference** when extracting contents from provided PDF later.
Do not copy exactly from these references when generating JSON output, ONLY study the reference PDF and the output structure. """),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""Okay, I have studied the example input PDF and the corresponding reference JSON output. I understand the expected structure, the types of content to extract, and how to represent them in the JSON format.

I will use this knowledge to process future PDF exam papers, ensuring that the generated JSON:

-   Follows the hierarchical structure of main questions, questions, and sub-questions.
-   Accurately extracts text, diagrams, tables, and answer spaces.
-   Segregates Malay and English text correctly.
-   Represents answer spaces with the appropriate format (line, multiple-choice, or blank-space) and attributes.
-   Includes marks for each question/sub-question where applicable.
-   Excludes answer spaces for Main Questions 9-11.
-   Maintains the original order of content as it appears in the PDF.

I am ready to receive and process the next PDF content.
"""),
            ],
        ),
        # Actual PDF
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    data=file,
                    mime_type="application/pdf",
                ),
                types.Part.from_text(text=f"Extract **Main Questions {start} to {end}** for this PDF"),
            ],
        ),
    ]
  
  generate_content_config = types.GenerateContentConfig(
    temperature=1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type="application/json",
    system_instruction=[
            types.Part.from_text(text="""Your task is to extract PDF files according to the rules, schema and example files given and MUST respond in valid JSON format.
Avoid null values at ALL COSTS."""),
        ]
  )
  
  response = client.models.generate_content(
    model = model,
    contents = fixed_contents,
    config = generate_content_config
  )
  
  print(response.usage_metadata)
  return response

def convert_pdf_to_part(pdf_file):
  pdf_content_base64 = base64.b64encode(pdf_file).decode("utf-8")
  return {"mime_type": "application/pdf", "data": pdf_content_base64}