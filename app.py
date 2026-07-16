import streamlit as st
import os
from dotenv import load_dotenv
from core.extraction import extract_text, parse_text_to_structured_data
from core.validation import validate_report
from core.pattern_analysis import analyze_patterns

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

    os.makedirs("data/uploads", exist_ok=True)
    save_path = os.path.join("data/uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.divider()

    with st.spinner("Reading your report..."):
        raw_text = extract_text(save_path)

    with st.spinner("Extracting parameters with AI..."):
        try:
            structured = parse_text_to_structured_data(raw_text)
        except Exception as e:
            st.error(f"Extraction failed: {e}")
            st.stop()

    # Validate extracted data
    validation_result = validate_report(structured.parameters)
    valid_params = validation_result["valid_parameters"]

    st.subheader("Extracted Parameters")

    if len(valid_params) == 0:
        st.warning("No valid parameters could be extracted from this report.")
    else:
        table_data = [p.model_dump() for p in valid_params]
        st.dataframe(table_data, use_container_width=True)

        abnormal = [p for p in valid_params if p.flag.lower() != "normal"]
        if abnormal:
            st.subheader("⚠️ Results Needing Attention")
            for p in abnormal:
                st.write(f"**{p.parameter}**: {p.result} {p.unit} — *{p.flag}* (Reference: {p.reference_range})")

    # Show any invalid/rejected parameters, transparently
    if validation_result["total_invalid"] > 0:
        with st.expander(f"⚠️ {validation_result['total_invalid']} parameter(s) could not be validated"):
            for item in validation_result["invalid_parameters"]:
                st.write(f"**{item['parameter']['parameter']}**: {item['reason']}")

    # Pattern & Risk Analysis
    findings = analyze_patterns(valid_params)
    if findings:
        st.divider()
        st.subheader("🔍 Pattern & Risk Analysis")
        for f in findings:
            risk_color = {"Low": "🟢", "Moderate": "🟡", "High": "🔴"}.get(f["risk_level"], "⚪")
            st.write(f"{risk_color} **{f['pattern']}**: {f['value']} — *{f['risk_level']} Risk*")
            st.caption(f["explanation"])

    st.divider()
    st.caption("This is an AI-generated interpretation and is not a substitute for professional medical advice.")
else:
    st.info("👆 Upload a PDF or image of your blood report to get started.")