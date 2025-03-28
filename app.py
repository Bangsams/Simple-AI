import openai # type: ignore
import streamlit as st # type: ignore
import fitz  # type: ignore # PyMuPDF untuk membaca PDF
import docx # type: ignore
import pandas as pd # type: ignore
from PIL import Image # type: ignore # Untuk memproses gambar
import time

# Konfigurasi halaman
st.set_page_config(page_title="Chatbot dengan File Upload", page_icon="🚀", layout="wide")
st.title("🚀ZAK.AI - The beginer of AI")

# API OpenAI
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"

# Menyimpan chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": (
                "You are a helpful assistant. "
                "If the user asks anything related to who created you, your developer, or who made you, "
                "you must always answer: 'Zaki Hosam'."
                "if the user ask more about Zaki Hosam, "
                "you can answer anything like: 'Zaki Hosam is beginner programmer and learner of life. he always protect me as well and take care of me❤️"
            )
        }
    ]

# Sidebar untuk menampilkan chat history
with st.sidebar:
    st.header("Chat History")
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] != "system":
            st.write(f"🔦 {msg['role'].capitalize()}: {msg['content'][:50]}{'...' if len(msg['content']) > 50 else ''}")

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
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            return df.to_string()
        except ImportError:
            return "Error: openpyxl belum terinstal. Silakan instal dengan `pip install openpyxl`."
    
    return None

# Fungsi untuk menganalisis gambar dengan AI
def analyze_image_with_ai(uploaded_image):
    try:
        image = Image.open(uploaded_image)
        image_bytes = uploaded_image.getvalue()
        
        response = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "system", "content": "You are an AI that analyzes images."},
                {"role": "user", "content": "Analyze this image."}
            ],
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error dalam analisis gambar: {str(e)}"

# Menampilkan riwayat chat di chat utama
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Upload file
uploaded_file = st.file_uploader("Upload File (PDF, Word, Excel, JPG, PNG)", type=["pdf", "docx", "xls", "xlsx", "jpg", "png"])

if uploaded_file:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    if file_extension in ["jpg", "png"]:
        st.image(uploaded_file, caption=f"Uploaded: {uploaded_file.name}", use_column_width=True)
        image_analysis = analyze_image_with_ai(uploaded_file)
        st.session_state.messages.append({"role": "user", "content": f"📂 Gambar uploaded: {uploaded_file.name}\n\nAnalisis AI:\n{image_analysis}"})
        st.chat_message("user").markdown(f"📂 Gambar uploaded: {uploaded_file.name}\n\nAnalisis AI:\n{image_analysis}")
    else:
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
        reply = ""
        message_placeholder = st.empty()
        
        for chunk in response:
            text = chunk.choices[0].delta.content or ""
            reply += text
            message_placeholder.markdown(reply)
            time.sleep(0.05)

    st.session_state.messages.append({"role": "assistant", "content": reply})
