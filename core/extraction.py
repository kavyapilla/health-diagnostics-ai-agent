import pdfplumber
from PIL import Image
import pytesseract
import json
from groq import Groq
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# Point pytesseract to the Tesseract install location on Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class BloodParameter(BaseModel):
    parameter: str
    result: str
    flag: str  # "Normal", "High", "Low", "Borderline"
    reference_range: str
    unit: str


class ExtractedReport(BaseModel):
    parameters: List[BloodParameter]


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts raw text from a PDF file using pdfplumber.
    """
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
    return full_text


def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from an image file (PNG/JPG) using Tesseract OCR.
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text


def extract_text(file_path: str) -> str:
    """
    Unified extraction function - detects file type and routes to
    the correct extraction method (PDF text extraction or OCR).
    """
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")


def parse_text_to_structured_data(raw_text: str) -> ExtractedReport:
    """
    Sends raw extracted text to Groq LLM and asks it to return
    structured JSON matching the BloodParameter schema.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""You are a medical data extraction assistant. Below is raw text extracted from a blood test report. Extract every test parameter into structured JSON.

For each parameter found, extract:
- parameter: the test name (e.g., "Hemoglobin (Hb)")
- result: the numeric result value (e.g., "12.5")
- flag: "Normal" if no flag is shown, otherwise "High", "Low", or "Borderline" exactly as shown
- reference_range: the reference range shown (e.g., "13.0-17.0")
- unit: the unit shown (e.g., "g/dL")

Ignore headers, lab info, doctor names, instrument info, and any non-parameter text.
IMPORTANT: This text may come from OCR and could have columns separated or misaligned (e.g., all parameter names listed first, followed by all values, followed by all reference ranges, in separate blocks rather than side-by-side). Carefully match each parameter name to its correct corresponding result value and reference range based on their ORDER of appearance, not just proximity. Section headers like "RBC COUNT" or "WBC COUNT" are category labels, not parameter names themselves - use the actual sub-item name instead (e.g., "Total RBC count", not "RBC COUNT"). If you cannot confidently match a parameter to its value, exclude it rather than guessing.

Return ONLY valid JSON in this exact format, nothing else:
{{"parameters": [{{"parameter": "...", "result": "...", "flag": "...", "reference_range": "...", "unit": "..."}}]}}

Raw text:
{raw_text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=4096,
            response_format={"type": "json_object"}
        )
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
        return ExtractedReport(**data)
    except Exception:
        # If the LLM fails to produce valid JSON (e.g. because the document
        # has no relevant medical parameters, or is too large/malformed),
        # treat it the same as "no parameters found" rather than crashing.
        return ExtractedReport(parameters=[])


if __name__ == "__main__":
    test_path = "data/test_reports/report_03_cbc_scanned.png"
    text = extract_text(test_path)
    print("--- OCR EXTRACTED TEXT ---")
    print(text)

    print("\n--- STRUCTURED DATA ---")
    structured = parse_text_to_structured_data(text)
    for param in structured.parameters:
        print(param.model_dump())