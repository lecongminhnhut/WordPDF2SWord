import os
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote

import requests
import streamlit as st

FRONTEND_DIR = Path(__file__).resolve().parent

# Backend API endpoints
UPLOAD_FILE_API_URL = "/upload-file"
GET_STANDARD_WORD_API_URL = "/get-standard-word"
GET_FILE_API_URL = "/get-file"

CONNECT_TIMEOUT_SECONDS = 10
UPLOAD_TIMEOUT_SECONDS = 120
PROCESS_TIMEOUT_SECONDS = 180
DOWNLOAD_TIMEOUT_SECONDS = 60

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
color: #1F2937;
margin: 20px 0px;
}}
[data-testid="stSidebarCollapsedControl"] {{
border-radius: 5px;
background-color: white;
color: #1F2937;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    st.image(FRONTEND_DIR / "assets" / "app_logo3.png", width=200)
with col2:
    st.title("PDF To Standard Word")

st.info("Tải lên file PDF cần chuyển thành Standard Word.")
st.warning(
    "Phiên bản hiện tại chỉ hỗ trợ PDF có lớp văn bản, bố cục một cột, "
    "chủ yếu bằng tiếng Việt và không có bảng, công thức, footnote/endnote "
    "phức tạp hoặc hình ảnh mang nội dung thiết yếu."
)

uploaded_files = st.file_uploader(
    label="Upload Files:",
    type=["pdf"],
    accept_multiple_files=True
)

uploaded_paths = []
processed_paths = []
fetched_files = []


def upload_file_to_backend(uploaded_file):
    try:
        file_buffer = BytesIO(uploaded_file.read())
        file_buffer.name = uploaded_file.name
        files = {
            "file": (uploaded_file.name, file_buffer, uploaded_file.type),
            "user_id": (
                None,
                str(st.session_state.get("session_state_id_turn", 0))
            )
        }
        response = requests.post(
            st.session_state.back_end_url + UPLOAD_FILE_API_URL,
            files=files,
            timeout=(CONNECT_TIMEOUT_SECONDS, UPLOAD_TIMEOUT_SECONDS)
        )
        if response.status_code == 201:
            return response.json().get("file_path")

        st.error(f"Không thể upload '{uploaded_file.name}': {response.text}")
    except requests.exceptions.Timeout:
        st.error(f"Upload '{uploaded_file.name}' bị quá thời gian. Hãy thử lại.")
    except requests.exceptions.RequestException as exc:
        st.error(f"Không thể kết nối backend khi upload '{uploaded_file.name}': {exc}")
    except Exception as exc:
        st.error(f"Lỗi khi upload '{uploaded_file.name}': {exc}")
    return None


def get_processed_file_path(file_path):
    try:
        response = requests.post(
            st.session_state.back_end_url + GET_STANDARD_WORD_API_URL,
            json={
                "user_id": st.session_state.get("session_state_id_turn", 0),
                "file_path": file_path
            },
            timeout=(CONNECT_TIMEOUT_SECONDS, PROCESS_TIMEOUT_SECONDS)
        )
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, str):
                return result
            return result.get("file_path")

        st.error(f"Không thể xử lý '{file_path}': {response.text}")
    except requests.exceptions.Timeout:
        st.error(
            f"Xử lý '{file_path}' vượt quá {PROCESS_TIMEOUT_SECONDS} giây. "
            "Hãy thử một tài liệu ngắn hơn."
        )
    except requests.exceptions.RequestException as exc:
        st.error(f"Không thể kết nối backend khi xử lý '{file_path}': {exc}")
    except Exception as exc:
        st.error(f"Lỗi khi xử lý '{file_path}': {exc}")
    return None


def fetch_file_from_backend(file_path):
    filename = ""
    try:
        decoded_path = unquote(file_path)
        filename = os.path.basename(decoded_path).strip()

        response = requests.get(
            f"{st.session_state.back_end_url + GET_FILE_API_URL}/{filename}",
            stream=True,
            timeout=(CONNECT_TIMEOUT_SECONDS, DOWNLOAD_TIMEOUT_SECONDS)
        )

        if response.status_code == 200:
            return BytesIO(response.content)

        st.error(f"Không thể tải file '{filename}': HTTP {response.status_code}")
    except requests.exceptions.Timeout:
        st.error(f"Tải file '{filename}' bị quá thời gian. Hãy thử lại.")
    except requests.exceptions.RequestException as exc:
        st.error(f"Không thể kết nối backend khi tải file: {exc}")
    except Exception as exc:
        st.error(f"Lỗi khi tải file: {exc}")
    return None


if uploaded_files:
    for uploaded_file in uploaded_files:
        uploaded_path = upload_file_to_backend(uploaded_file)
        if uploaded_path:
            uploaded_paths.append(uploaded_path)

if st.button("Get Standard Word"):
    if not uploaded_paths:
        st.warning("Vui lòng upload ít nhất một file PDF.")
        st.stop()

    for path in uploaded_paths:
        processed_path = get_processed_file_path(path)
        if processed_path:
            processed_paths.append(processed_path)

    for path in processed_paths:
        fetched_file = fetch_file_from_backend(path)
        if fetched_file:
            fetched_files.append((fetched_file, os.path.basename(path)))

if fetched_files:
    st.write("Processed Files:")
    for i, (file_data, filename) in enumerate(fetched_files, 1):
        safe_filename = os.path.basename(filename)
        st.download_button(
            label=f"Download Processed File {i}: {safe_filename}",
            data=file_data,
            file_name=safe_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
