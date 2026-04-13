import os
from pathlib import Path
from streamlit.runtime.uploaded_file_manager import UploadedFile

def get_file_extension(file_name: str) -> str:
    """
    Returns the suffix of an uploaded file
    """
    return Path(file_name).suffix.lower()

def create_folder_for_upload(parent_folder_path: str, folder_name: str) -> str:
    """
    Creates an child folder inside a specified parent's folder to store a file upload and returns its path
    """
    folder_path = os.path.join(parent_folder_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def create_path_for_uploaded_file(folder_path: str, uploaded_file: UploadedFile) -> str:
    """
    Creates and returns a full file path for an uploaded file
    """
    return os.path.join(folder_path, uploaded_file.name)

def save_uploaded_file(uploaded_file: UploadedFile, file_path: str) -> None:
    """
    Reads the content of an uploaded file and stores it at a specified location
    """
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())