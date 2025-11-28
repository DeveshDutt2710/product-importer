import os
import tempfile
from pathlib import Path

from products.constants import ProductConstants


def validate_csv_file(uploaded_file):
    if not uploaded_file:
        raise ValueError("No file provided")
    
    file_name = uploaded_file.name
    file_extension = Path(file_name).suffix.lower()
    
    if file_extension not in ProductConstants.CSV_ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type. Only {ProductConstants.CSV_ALLOWED_EXTENSIONS} are allowed")
    
    if uploaded_file.size > ProductConstants.CSV_MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed size of {ProductConstants.CSV_MAX_FILE_SIZE / (1024 * 1024)} MB")
    
    return True


def save_uploaded_file_to_temp(uploaded_file):
    validate_csv_file(uploaded_file)
    
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"csv_import_{uploaded_file.name}")
    
    with open(temp_file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    
    return temp_file_path

