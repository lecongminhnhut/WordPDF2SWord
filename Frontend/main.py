import json
import streamlit as st
import requests  # Import requests for API calls

BACK_END_URL = "http://localhost:5000" #"https://badger-prepared-iguana.ngrok-free.app"
REGISTER_USER_API_URL = "/register-user"
DELETE_USER_DATA_API_URL = "/delete-user"

st.set_page_config(page_title="WordPdf2Sword", page_icon=":material/edit:")

if "back_end_url" not in st.session_state:
    st.session_state.back_end_url = BACK_END_URL

# Call backend API to register user and store the ID
if "session_state_id_turn" not in st.session_state:
    try:
        response = requests.post(st.session_state.back_end_url + REGISTER_USER_API_URL)
        if response.status_code == 201:
            st.session_state.session_state_id_turn = response.json().get("user_id")
        else:
            st.error(f"Error registering user: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the server: {e}")

@st.cache_resource
def get_img():
    print("Loading images...")
    with open('./assets/img_map.json', 'r') as f:
        index = json.load(f)
    return index

index = get_img()

st.session_state.index = index

sidebar_pg = f"""
<style>
[data-testid="stSidebarNav"] {{
border-radius: 20px;
padding: 10px 0px;
background-color: white;
margin: 10px;
}}
[data-testid="stSidebarNavSeparator"] {{
padding: 0px;
margin: 0px 10px;
}}
[data-testid="stSidebarUserContent"] {{
border-radius: 20px;
padding: 10px;
background-color: white;
margin: 5px;
}}
[data-testid="stSidebarCollapseButton"] {{
border-radius: 5px;
background-color: white;
}}
</style>
"""
st.markdown(sidebar_pg, unsafe_allow_html=True)

WordPdf2Sword = st.Page("wordpdf2sword.py", title="Word|Pdf To Standard Word", icon="🔍")

# JavaScript to detect tab closure and send `user_id` to the backend
js_code = f"""
<script>
    window.addEventListener("beforeunload", function (event) {{
        const data = {{
            user_id: {st.session_state.session_state_id_turn}
        }};
        
        fetch("{st.session_state.back_end_url}{DELETE_USER_DATA_API_URL}", {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify(data),
            // Using keepalive to ensure the request completes even if the page is unloading
            keepalive: true
        }}).catch(error => console.error('Error:', error));
    }});
</script>
"""

# # Embed the JavaScript in the Streamlit app
# st.components.v1.html(js_code)

pg = st.navigation([WordPdf2Sword])
pg.run()