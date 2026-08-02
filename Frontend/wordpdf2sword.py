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

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
background-color: #E8EEF5;
}}
[data-testid="stHeader"] {{
background: rgba(0, 0, 0, 0);
}}
[data-testid="stStatusWidget"] {{
display: none;
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

STATE_DEFAULTS = {
    "operation_in_progress": False,
    "upload_requested": False,
    "process_requested": False,
    "uploaded_paths": [],
    "processed_files": [],
    "operation_message": None,
}
for state_key, default_value in STATE_DEFAULTS.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


def request_upload():
    st.session_state.operation_in_progress = True
    st.session_state.upload_requested = True
    st.session_state.process_requested = False
    st.session_state.uploaded_paths = []
    st.session_state.processed_files = []
    st.session_state.operation_message = None


def request_processing():
    st.session_state.operation_in_progress = True
    st.session_state.process_requested = True
    st.session_state.processed_files = []
    st.session_state.operation_message = None


is_busy = st.session_state.operation_in_progress
uploaded_files = st.file_uploader(
    label="Upload Files:",
    type=["pdf"],
    accept_multiple_files=True,
    key="uploaded_pdf_files",
    on_change=request_upload,
    disabled=is_busy,
)

st.button(
    "Get Standard Word",
    on_click=request_processing,
    disabled=is_busy or not st.session_state.uploaded_paths,
)

status_container = st.container()

operation_message = st.session_state.operation_message
if operation_message:
    message_type, message_text = operation_message
    if message_type == "success":
        st.success(message_text)
    else:
        st.warning(message_text)


def upload_file_to_backend(uploaded_file):
    try:
        file_buffer = BytesIO(uploaded_file.getvalue())
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


if st.session_state.upload_requested:
    files_to_upload = list(uploaded_files or [])
    uploaded_paths = []

    if files_to_upload:
        with status_container:
            with st.status(
                f"Đang tải {len(files_to_upload)} file PDF lên máy chủ...",
                expanded=True,
            ) as upload_status:
                for uploaded_file in files_to_upload:
                    st.write(f"Đang tải: {uploaded_file.name}")
                    uploaded_path = upload_file_to_backend(uploaded_file)
                    if uploaded_path:
                        uploaded_paths.append(uploaded_path)

                uploaded_count = len(uploaded_paths)
                if uploaded_count == len(files_to_upload):
                    upload_status.update(
                        label=f"Đã tải lên {uploaded_count} file PDF.",
                        state="complete",
                        expanded=False,
                    )
                    st.session_state.operation_message = (
                        "success",
                        f"Đã tải lên {uploaded_count} file PDF. Bạn có thể bắt đầu xử lý.",
                    )
                else:
                    upload_status.update(
                        label=(
                            f"Chỉ tải lên thành công {uploaded_count}/"
                            f"{len(files_to_upload)} file PDF."
                        ),
                        state="error",
                        expanded=True,
                    )
                    st.session_state.operation_message = (
                        "warning",
                        f"Chỉ tải lên thành công {uploaded_count}/{len(files_to_upload)} file PDF.",
                    )

    st.session_state.uploaded_paths = uploaded_paths
    st.session_state.upload_requested = False
    st.session_state.operation_in_progress = False
    st.rerun()

if st.session_state.process_requested:
    uploaded_paths = list(st.session_state.uploaded_paths)
    processed_paths = []
    fetched_files = []

    with status_container:
        with st.status(
            f"Đang xử lý {len(uploaded_paths)} tài liệu. Vui lòng không đóng trang...",
            expanded=True,
        ) as process_status:
            for path in uploaded_paths:
                st.write(f"Đang phân tích cấu trúc: {os.path.basename(path)}")
                processed_path = get_processed_file_path(path)
                if processed_path:
                    processed_paths.append(processed_path)

            for path in processed_paths:
                st.write(f"Đang tải file kết quả: {os.path.basename(path)}")
                fetched_file = fetch_file_from_backend(path)
                if fetched_file:
                    fetched_files.append((
                        fetched_file.getvalue(),
                        os.path.basename(path),
                    ))

            completed_count = len(fetched_files)
            if completed_count == len(uploaded_paths):
                process_status.update(
                    label=f"Đã xử lý xong {completed_count} tài liệu.",
                    state="complete",
                    expanded=False,
                )
                st.session_state.operation_message = (
                    "success",
                    f"Đã xử lý xong {completed_count} tài liệu. File đã sẵn sàng để tải xuống.",
                )
            else:
                process_status.update(
                    label=(
                        f"Chỉ xử lý thành công {completed_count}/"
                        f"{len(uploaded_paths)} tài liệu."
                    ),
                    state="error",
                    expanded=True,
                )
                st.session_state.operation_message = (
                    "warning",
                    f"Chỉ xử lý thành công {completed_count}/{len(uploaded_paths)} tài liệu.",
                )

    st.session_state.processed_files = fetched_files
    st.session_state.process_requested = False
    st.session_state.operation_in_progress = False
    st.rerun()

if st.session_state.processed_files:
    st.write("Processed Files:")
    for i, (file_data, filename) in enumerate(
        st.session_state.processed_files,
        1,
    ):
        safe_filename = os.path.basename(filename)
        st.download_button(
            label=f"Download Processed File {i}: {safe_filename}",
            data=file_data,
            file_name=safe_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=st.session_state.operation_in_progress,
        )
