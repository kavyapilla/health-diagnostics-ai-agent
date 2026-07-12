import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Health Diagnostics AI", page_icon="🩸", layout="centered")

st.title("🩸 Health Diagnostics AI")
st.write("Upload your blood report to get an AI-powered interpretation and personalized health recommendations.")

st.divider()

uploaded_file = st.file_uploader(
    "Upload your blood report",
    type=["pdf", "png", "jpg", "jpeg"],
    help="Supported formats: PDF, PNG, JPG"
)

if uploaded_file is not None:
    st.success(f"File uploaded: **{uploaded_file.name}**")
    st.write(f"File size: {round(uploaded_file.size / 1024, 1)} KB")
    st.write(f"File type: {uploaded_file.type}")

    # Save the uploaded file temporarily so later steps can process it
    os.makedirs("data/uploads", exist_ok=True)
    save_path = os.path.join("data/uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info(f"File saved locally for processing at: `{save_path}`")

    st.divider()
    st.write("**Next step:** Extraction and interpretation coming soon.")
else:
    st.info("👆 Upload a PDF or image of your blood report to get started.")