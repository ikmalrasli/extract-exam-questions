import json
import logging

def build_extract_section_data_prompt(section_info: dict):
    reference_sections = {
        'Section A': {'file': 'reference_files/with_sections/reference_output_A.json', 'start_page': 4, 'end_page': 26},
        'Section B': {'file': 'reference_files/with_sections/reference_output_B.json', 'start_page': 27, 'end_page': 32},
        'Section C': {'file': 'reference_files/with_sections/reference_output_C.json', 'start_page': 33, 'end_page': 35}
    }
    reference_config = reference_sections.get(section_info['name'])
    
    if not reference_config:
        raise ValueError(f"Unknown section name: {section_info['name']}")
        
    try:
        with open(reference_config['file'], 'r', encoding='utf-8') as f:
            reference_structure = f.read()
    except FileNotFoundError:
        raise ValueError(f"Reference file not found: {reference_config['file']}")

    question_range = ""
    if section_info['name'] == 'Bahagian A' or section_info['name'] == 'Section A':
        question_range = "1-8"
    elif section_info['name'] == 'Bahagian B' or section_info['name'] == 'Section B':
        question_range = "9-10"
    elif section_info['name'] == 'Bahagian C' or section_info['name'] == 'Section C':
        question_range = "11"

    section_prompt = f"""
        You are an Exam Paper Structure Extractor. Your task is to create a valid JSON structure from the PDF content.

        IMPORTANT JSON STRUCTURE RULES:
        1. Each question should appear EXACTLY ONCE in the structure
        2. DO NOT create nested duplicate questions
        3. DO NOT create recursive question structures
        4. Questions should follow this exact hierarchy:
           - main_questions (array)
             - number (string)
             - content_flow (array)
             - questions (array)
               - sub_questions (array) [if applicable]
        5. Every JSON object must be properly closed
        6. All arrays and objects must have proper comma delimiters
        7. All property names and string values must be in double quotes

        TASK STEPS:
        1. ANALYZE the provided PDF content for {section_info['name']}, Pages {section_info['start_page']} to {section_info['end_page']}
        2. Extract questions {question_range}
        3. Follow the JSON structure format shown here: {reference_structure}
        4. Use ONLY content from the provided PDF.
        5. **DO NOT COPY CONTENT FROM REFERENCE JSON**
        
        REQUIREMENTS:
        - Return ONLY valid JSON
        - NO explanations or markdown
        - NO extra backslashes
        - Each question should appear in exactly ONE place in the hierarchy
        - Verify all brackets and braces are properly matched
        - Ensure all required commas are present between elements
        - Extract actual content from PDF, do not use reference data
        - Keep only the structure format from reference, populate with PDF content

        Generate the JSON structure now.
    """
    return section_prompt

# Validate if Sections A, B, C has all the required questions
def validate_section_content(section_data: str, section_name: str) -> None:
    # Validate section content meets requirements.
    try:
        # Parse the JSON string into a dictionary
        data = json.loads(section_data)
        
        if section_name in ['Bahagian A', 'Section A']:
            # Check number of main questions
            main_questions = data.get('main_questions', [])
            question_numbers = [str(q.get('number')) for q in main_questions]  # Convert to strings
            expected_numbers = [str(i) for i in range(1, 9)]  # 1 to 8
            
            missing = set(expected_numbers) - set(question_numbers)
            if missing:
                logging.warning(f"Section A is missing questions: {', '.join(missing)}")
                # No longer raising an error, just logging a warning
        
        if section_name in ['Bahagian B', 'Section B']:
            # Check number of main questions
            main_questions = data.get('main_questions', [])
            question_numbers = [str(q.get('number')) for q in main_questions]
            expected_numbers = [str(i) for i in range(9, 11)]  # 9 to 10
            
            missing = set(expected_numbers) - set(question_numbers)
            if missing:
                logging.warning(f"Section B is missing questions: {', '.join(missing)}")
        
        if section_name in ['Bahagian C', 'Section C']:
            # Check number of main questions
            main_questions = data.get('main_questions', [])
            question_numbers = [str(q.get('number')) for q in main_questions]
            expected_numbers = ['11']
            missing = set(expected_numbers) - set(question_numbers)
            if missing:
                logging.warning(f"Section C is missing questions: {', '.join(missing)}")
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format: {str(e)}")
        # Still raise error for invalid JSON as this is a critical error
        raise
