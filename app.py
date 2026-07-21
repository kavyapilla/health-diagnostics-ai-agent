import streamlit as st
import os
from dotenv import load_dotenv
from core.extraction import extract_text, parse_text_to_structured_data
from core.validation import validate_report
from core.pattern_analysis import analyze_patterns
from core.context_analysis import apply_context
from core.synthesis import synthesize_findings
from core.report import generate_pdf_report

load_dotenv()

st.set_page_config(page_title="Health Diagnostics AI", page_icon="🩸", layout="centered")

st.title("🩸 Health Diagnostics AI")
st.write("Upload your blood report to get an AI-powered interpretation and personalized health recommendations.")

st.divider()

with st.expander("👤 Add your details for more personalized results (optional)"):
    col1, col2 = st.columns(2)
    with col1:
        user_age = st.number_input("Age", min_value=0, max_value=120, value=None, placeholder="e.g. 28")
    with col2:
        user_gender = st.selectbox("Gender", options=["Prefer not to say", "Male", "Female"])

uploaded_file = st.file_uploader(
    "Upload your blood report",
    type=["pdf", "png", "jpg", "jpeg"],
    help="Supported formats: PDF, PNG, JPG"
)

if uploaded_file is not None:
    # Guard: empty file
    if uploaded_file.size == 0:
        st.error("The uploaded file appears to be empty. Please upload a valid file.")
        st.stop()

    st.success(f"File uploaded: **{uploaded_file.name}**")

    os.makedirs("data/uploads", exist_ok=True)
    save_path = os.path.join("data/uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.divider()

    # Step 1: Extraction (raw text)
    with st.spinner("Reading your report..."):
        try:
            raw_text = extract_text(save_path)
        except Exception as e:
            st.error(
                "We couldn't read this file. It may be corrupted, password-protected, "
                "or in an unsupported format. Please try a different file."
            )
            st.caption(f"Technical details: {e}")
            st.stop()

    # Guard: no readable text at all
    if not raw_text or len(raw_text.strip()) < 20:
        st.error(
            "We couldn't find any readable text in this file. If this is a scanned image, "
            "try uploading a clearer, higher-resolution photo or scan."
        )
        st.stop()

    # Step 2: Structured extraction (LLM)
    with st.spinner("Extracting parameters with AI..."):
        try:
            structured = parse_text_to_structured_data(raw_text)
        except Exception as e:
            st.error(
                "Something went wrong while analyzing your report. This could be a temporary "
                "issue with the AI service. Please try again in a moment."
            )
            st.caption(f"Technical details: {e}")
            st.stop()

    # Guard: no parameters found at all - likely not a blood report
    if len(structured.parameters) == 0:
        st.warning(
            "We couldn't identify any blood test parameters in this document. "
            "Please make sure you've uploaded a blood test report, and that the image/PDF "
            "is clear and readable."
        )
        st.stop()

    # Step 3: Validation
    validation_result = validate_report(structured.parameters)
    valid_params = validation_result["valid_parameters"]

    st.subheader("Extracted Parameters")

    if len(valid_params) == 0:
        st.error(
            "We extracted some data, but none of it passed our quality checks. "
            "This usually happens with low-quality scans. Please try uploading a clearer image or the original PDF."
        )
        if validation_result["invalid_parameters"]:
            with st.expander("See what we found (and why it was rejected)"):
                for item in validation_result["invalid_parameters"]:
                    st.write(f"**{item['parameter']['parameter']}**: {item['reason']}")
        st.stop()

    table_data = [p.model_dump() for p in valid_params]
    st.dataframe(table_data, use_container_width=True)

    abnormal = [p for p in valid_params if p.flag.lower() != "normal"]
    if abnormal:
        st.subheader("⚠️ Results Needing Attention")
        for p in abnormal:
            st.write(f"**{p.parameter}**: {p.result} {p.unit} — *{p.flag}* (Reference: {p.reference_range})")

    if validation_result["total_invalid"] > 0:
        with st.expander(f"⚠️ {validation_result['total_invalid']} parameter(s) could not be validated"):
            for item in validation_result["invalid_parameters"]:
                st.write(f"**{item['parameter']['parameter']}**: {item['reason']}")
            st.caption(
                "These were excluded from analysis because the extracted data didn't pass "
                "our quality checks (e.g., missing or unreadable values)."
            )

    # Step 4: Contextual Analysis (Model 3)
    context_notes = []
    if user_gender != "Prefer not to say":
        context_notes = apply_context(valid_params, age=user_age, gender=user_gender)
        if context_notes:
            st.divider()
            st.subheader("👤 Personalized Interpretation")
            for note in context_notes:
                st.write(f"**{note['parameter']}**: {note['original_flag']} → **{note['adjusted_flag']}**")
                st.caption(note['explanation'])

    # Step 5: Pattern & Risk Analysis (Model 2)
    findings = analyze_patterns(valid_params)
    if findings:
        st.divider()
        st.subheader("🔍 Pattern & Risk Analysis")
        for f in findings:
            risk_color = {"Low": "🟢", "Moderate": "🟡", "High": "🔴"}.get(f["risk_level"], "⚪")
            st.write(f"{risk_color} **{f['pattern']}**: {f['value']} — *{f['risk_level']} Risk*")
            st.caption(f["explanation"])

    # Step 6: Synthesis & Recommendations
    st.divider()
    with st.spinner("Generating your personalized summary..."):
        try:
            synthesis = synthesize_findings(
                valid_params,
                findings,
                context_notes,
                age=user_age,
                gender=user_gender if user_gender != "Prefer not to say" else None
            )
            st.subheader("📋 Summary")
            st.write(synthesis.summary)

            st.subheader("✅ Personalized Recommendations")
            for rec in synthesis.recommendations:
                st.write(f"• {rec}")

            # Step 7: PDF Report Generation
            st.divider()
            try:
                pdf_bytes = generate_pdf_report(
                    valid_params,
                    findings,
                    context_notes,
                    synthesis.summary,
                    synthesis.recommendations,
                    age=user_age,
                    gender=user_gender if user_gender != "Prefer not to say" else None
                )
                st.download_button(
                    label="📄 Download Full Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"health_report_{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.warning("Your results are ready above, but we couldn't generate a downloadable PDF right now.")
                st.caption(f"Technical details: {e}")

        except Exception as e:
            st.warning(
                "We've extracted and analyzed your results above, but couldn't generate an AI summary "
                "at this time. This may be a temporary issue - your extracted data is still accurate above."
            )
            st.caption(f"Technical details: {e}")

    st.divider()
    st.caption("This is an AI-generated interpretation and is not a substitute for professional medical advice.")
else:
    st.info("👆 Upload a PDF or image of your blood report to get started.")