import json
import time
import streamlit as st
from io import BytesIO
import requests
import os
from urllib.parse import unquote

# Backend API endpoints
UPLOAD_FILE_API_URL = "/upload-file"  # Endpoint for uploading files
GET_STANDARD_WORD_API_URL = "/get-standard-word"  # Endpoint to get processed file paths
GET_FILE_API_URL = "/get-file"  # Endpoint to fetch processed files

background_img = st.session_state.index["app_background4"]

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
background-image: url('data:image/png;base64,{background_img}');
background-size: cover;
background-repeat: no-repeat;
}}
[data-testid="stHeader"] {{
background: rgba(0, 0, 0, 0);
}}
[data-testid="stMainBlockContainer"]{{
border: 15px solid white;
border-radius: 20px;
padding: 5px;
background-color: white;
margin: 20px 0px;
}}
[data-testid="stSidebarCollapsedControl"] {{
border-radius: 5px;
background-color: white;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    st.image('./assets/app_logo3.png', width=200)
with col2:
    st.title("Word|PDF To Standard Word")

st.info("Upload Word or PDF files you want to process💖")

# File uploader
uploaded_files = st.file_uploader(
    label="Upload Files:",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

uploaded_paths = []  # Store paths of uploaded files
processed_paths = []  # Store paths of processed files
fetched_files = []  # Store downloaded files

# Function to upload files to the backend
def upload_file_to_backend(uploaded_file):
    try:
        file_buffer = BytesIO(uploaded_file.read())
        file_buffer.name = uploaded_file.name  # Set the name for the file
        files = {
            "file": (uploaded_file.name, file_buffer, uploaded_file.type),
            "user_id": (None, str(st.session_state.get("session_state_id_turn", 0)))  # Ensure user_id is a string
        }
        response = requests.post(st.session_state.back_end_url + UPLOAD_FILE_API_URL, files=files)
        if response.status_code == 201:
            return response.json().get("file_path")  # Return the saved file path
        else:
            st.error(f"Failed to upload '{uploaded_file.name}': {response.text}")
    except Exception as e:
        st.error(f"Error uploading file '{uploaded_file.name}': {e}")
    return None

# Function to get the processed file path for a file
def get_processed_file_path(file_path):
    try:
        response = requests.post(
            st.session_state.back_end_url + GET_STANDARD_WORD_API_URL,
            json={"user_id": st.session_state.get("session_state_id_turn", 0),
                  "file_path": file_path}
        )
        if response.status_code == 200:
            return response.text  # Return the processed file path
        else:
            st.error(f"Failed to process file '{file_path}': {response.text}")
    except Exception as e:
        st.error(f"Error processing file '{file_path}': {e}")
    return None

# Function to fetch a processed file from the backend
def fetch_file_from_backend(file_path):
    try:
        # Decode the URL-encoded path and extract the filename
        decoded_path = unquote(file_path)  # Decode any URL-encoded characters
        filename = os.path.basename(decoded_path).strip()  # Extract the filename and clean it

        # Debugging to verify the filename
        print(f"Decoded path: {decoded_path}")
        print(f"Extracted filename: {filename}")

        # Make the GET request to the backend
        response = requests.get(f"{st.session_state.back_end_url + GET_FILE_API_URL}/{filename}", stream=True)
        
        if response.status_code == 200:
            return BytesIO(response.content)  # Return the file as a BytesIO object
        else:
            st.error(f"Failed to fetch file '{filename}': {response.status_code}")
    except Exception as e:
        st.error(f"Error fetching file: {e}")
    return None

# Process uploaded files
if uploaded_files:
    for uploaded_file in uploaded_files:
        uploaded_path = upload_file_to_backend(uploaded_file)
        if uploaded_path:
            uploaded_paths.append(uploaded_path)

# Button to process files and fetch results
if st.button("Get Standard Word"):
    if not uploaded_paths:
        st.warning("Please upload Word or PDF files")
        st.stop()

    # Get processed file paths
    for path in uploaded_paths:
        processed_path = get_processed_file_path(path)
        if processed_path:
            processed_paths.append(processed_path)

    # Fetch processed files
    for path in processed_paths:
        fetched_file = fetch_file_from_backend(path)
        if fetched_file:
            fetched_files.append((fetched_file, path.split("/")[-1]))  # Store file and its name

# Display fetched files
if fetched_files:
    st.write("Processed Files:")
    for i, (file_data, filename) in enumerate(fetched_files, 1):
        safe_filename = filename.split("/")[-1]  # Extract only the filename
        st.download_button(
            label=f"Download Processed File {i}: {safe_filename}",
            data=file_data,
            file_name="safe_filename.docx",
        )