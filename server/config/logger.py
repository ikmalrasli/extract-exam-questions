from datetime import datetime
import json

def log_json(json_data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_log_name = f'json_log_{timestamp}.json'

    # 🔍 Ensure `json_data` is a valid JSON structure
    if isinstance(json_data, list) and all(isinstance(item, str) for item in json_data):
        # Convert each string entry to a dictionary
        json_data = [json.loads(item) for item in json_data]
    elif isinstance(json_data, str):
        try:
            json_data = json.loads(json_data)  # Convert single JSON string to dict
        except json.JSONDecodeError:
            print("❌ Invalid JSON string provided!")
            return

    # 🔄 Merge all "main_questions" into one list
    if isinstance(json_data, list):  # If input is a list of objects
        combined_main_questions = [q for entry in json_data if "main_questions" in entry for q in entry["main_questions"]]
        json_data = {"main_questions": combined_main_questions}

    # 📝 Save merged JSON
    with open(json_log_name, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Merged JSON saved to {json_log_name}")

def log_error(error_message: str, response_text: str = None) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_log_name = f'error_logs/error_log_{timestamp}.log'
    
    with open(error_log_name, "w", encoding='utf-8') as f:
        f.write(f"Error: {error_message}\n\n")
        if response_text:
            f.write(f"Response text:\n{response_text}")
    
    print(f"❌ Error logged to {error_log_name}")