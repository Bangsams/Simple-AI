from openai import OpenAI # type: ignore
import openai # type: ignore
import streamlit as st # type: ignore
import fitz  # type: ignore # PyMuPDF untuk membaca PDF
import docx # type: ignore
import pandas as pd # type: ignore

# Konfigurasi halaman
st.set_page_config(page_title="Chatbot dengan File Upload", page_icon="💬", layout="wide")
st.title("ZAK.AI")

# API OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

# Menyimpan chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant"}]

# Sidebar untuk menampilkan chat history
with st.sidebar:
    st.header("Chat History")
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] != "system":
            st.write(f"🗨️ {msg['role'].capitalize()}: {msg['content'][:50]}{'...' if len(msg['content']) > 50 else ''}")

# Fungsi untuk membaca teks dari file
def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return None

    file_extension = uploaded_file.name.split(".")[-1].lower()
    if file_extension == "pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    
    elif file_extension in ["doc", "docx"]:
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    
    elif file_extension in ["xls", "xlsx"]:
        df = pd.read_excel(uploaded_file)
        return df.to_string()
    
    return None

# Menampilkan riwayat chat di chat utama
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Upload file
uploaded_file = st.file_uploader("Upload File (PDF, Word, Excel)", type=["pdf", "docx", "xls", "xlsx"])

if uploaded_file:
    file_text = extract_text_from_file(uploaded_file)
    if file_text:
        st.session_state.messages.append({"role": "user", "content": f"📂 File uploaded: {uploaded_file.name}\n\n{file_text}"})
        st.chat_message("user").markdown(f"📂 File uploaded: {uploaded_file.name}\n\n{file_text}")
    else:
        st.warning("File tidak dapat dianalisis atau tidak mengandung teks.")

# Input dari pengguna
if prompt := st.chat_input("Ketik pesan..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Respon AI
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )
        reply = "".join(chunk.choices[0].delta.content or "" for chunk in response)
        st.markdown(reply)
    
    st.session_state.messages.append({"role": "assistant", "content": reply})
