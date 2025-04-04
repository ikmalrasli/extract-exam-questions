from ultralytics import YOLO
import cv2
import torch
import os
import json
from pdf2image import convert_from_bytes
import numpy as np

# Extract relevant pages from JSON
def extract_relevant_pages(json_obj):
    """
    Extracts all unique pages containing diagrams/tables from the JSON.
    """
    relevant_pages = set()

    def recurse(obj):
        if isinstance(obj, list):
            for item in obj:
                recurse(item)
        elif isinstance(obj, dict):
            if "page" in obj and "number" in obj:
                # Convert page to integer before adding to the set
                try:
                    relevant_pages.add(int(obj["page"]))
                except ValueError:
                    print(f"Warning: Page number '{obj['page']}' is not a valid integer.")
            for key in ["content_flow", "questions", "subquestions", "items"]:
                if key in obj and isinstance(obj[key], list):
                    recurse(obj[key])

    recurse(json_obj.get("main_questions", []))
    return sorted(relevant_pages)  # Sort to process pages in order

# Add this new function to get diagram/table numbers for a specific page
def get_page_object_numbers(json_obj, page):
    """
    Returns a list of tuples (number, type) for all diagrams/tables on a specific page
    sorted by their number.
    """
    objects = []
    
    def recurse(obj):
        if isinstance(obj, list):
            for item in obj:
                recurse(item)
        elif isinstance(obj, dict):
            if obj.get("page") == page and obj.get("type") in ["diagram", "table"]:
                # Get the actual number from the object
                number = obj.get("number")
                if number:  # Only add if number exists
                    objects.append((number, obj.get("type")))
                else:
                    print(f"Warning: Object on page {page} has no number.")
            for key in ["content_flow", "questions", "subquestions", "items"]:
                if key in obj and isinstance(obj[key], list):
                    recurse(obj[key])
    
    recurse(json_obj.get("main_questions", []))
    
    # Debugging output
    if not objects:
        print(f"No expected objects found for page {page}.")
    else:
        print(f"Expected objects for page {page}: {objects}")
    
    return objects  # Remove the sort since we want to maintain JSON order

# Add this function before the page processing loop
def sort_boxes_by_position(boxes, y_threshold=50):
    """
    Sort boxes by position, grouping them into rows based on y-coordinate proximity.
    Args:
        boxes: List of ((y1, x1), (x1, y1, x2, y2), type) tuples
        y_threshold: Maximum y-difference to consider boxes in the same row
    """
    # First, group boxes into rows
    rows = []
    current_row = []
    sorted_by_y = sorted(boxes, key=lambda x: x[0][0])  # Sort by y1
    
    for box in sorted_by_y:
        if not current_row or abs(box[0][0] - current_row[0][0][0]) <= y_threshold:
            current_row.append(box)
        else:
            # Sort current row by x-coordinate
            rows.append(sorted(current_row, key=lambda x: x[0][1]))
            current_row = [box]
    
    if current_row:
        rows.append(sorted(current_row, key=lambda x: x[0][1]))
    
    # Flatten the rows
    return [box for row in rows for box in row]

# Update JSON with the URL
def update_json_with_url(json_obj, page, obj_type, detected_number, file_name):
    """
    Finds the correct diagram/table entry in json_data and updates it with the URL.
    """
    def recurse(obj):
        if isinstance(obj, list):
            for item in obj:
                recurse(item)
        elif isinstance(obj, dict):
            # Match by page number, type, and number
            if (obj.get("page") == page and 
                obj.get("type") == obj_type and 
                obj.get("number") == detected_number):
                obj["url"] = file_name
                return
            for key in ["content_flow", "questions", "subquestions", "items"]:
                if key in obj and isinstance(obj[key], list):
                    recurse(obj[key])

    recurse(json_obj.get("main_questions", []))

def get_images(pdf_file, json_data):
    print("Get images...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model = YOLO(os.path.join(base_dir, "..", "assets", "my_model.pt"))  # Change to your trained model path

    # Check if CUDA (GPU) is available, else use CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    
    relevant_pages = extract_relevant_pages(json_data)
    print('relevant pages:', relevant_pages)

    # Convert the uploaded PDF file to images
    pages = convert_from_bytes(pdf_file, dpi=300)  # Higher DPI for better quality

    cropped_images = []  # List to hold cropped images and their metadata

    for page_num in relevant_pages:
        if page_num > len(pages):  # Skip if page number is out of bounds
            continue

        # Convert PIL image to OpenCV format
        image = cv2.cvtColor(np.array(pages[page_num - 1]), cv2.COLOR_RGB2BGR)

        # Run YOLO inference
        results = model(image, conf=0.5)  # Adjust confidence threshold if needed

        detected_boxes = []
        for result in results:
            for i, box in enumerate(result.boxes.xyxy):
                class_id = int(result.boxes.cls[i])
                if model.names[class_id] in ['diagram', 'table']:
                    x1, y1, x2, y2 = map(int, box)
                    detected_boxes.append(((y1, x1), (x1, y1, x2, y2), model.names[class_id]))

        detected_boxes = sort_boxes_by_position(detected_boxes)
        page_objects = get_page_object_numbers(json_data, page_num)
        
        print(f"Processing Page: {page_num}, Detected: {len(detected_boxes)}, Expected: {len(page_objects)}")
        for (expected_num, expected_type), (_, box, detected_type) in zip(page_objects, detected_boxes):
            if detected_type != expected_type:
                print(f"Warning: Type mismatch on page {page_num}: expected {expected_type}, detected {detected_type}")
                continue
            
            x1, y1, x2, y2 = box
            cropped_object = image[y1:y2, x1:x2]

            # Store cropped image and its metadata
            cropped_images.append((cropped_object, expected_num, expected_type, page_num))

    return cropped_images  # Return the list of cropped images and their metadata
