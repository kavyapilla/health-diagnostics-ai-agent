import pdfplumber

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts raw text from a PDF file using pdfplumber.
    Returns the full text content as a single string.
    """
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
    return full_text


if __name__ == "__main__":
    # Quick manual test - run this file directly to check extraction works
    test_path = "data/test_reports/report_01_drlogy_cbc.pdf"
    text = extract_text_from_pdf(test_path)
    print("--- EXTRACTED TEXT ---")
    print(text)

import json
from groq import Groq
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class BloodParameter(BaseModel):
    parameter: str
    result: str
    flag: str  # "Normal", "High", "Low", "Borderline"
    reference_range: str
    unit: str

class ExtractedReport(BaseModel):
    parameters: List[BloodParameter]


def parse_text_to_structured_data(raw_text: str) -> ExtractedReport:
    """
    Sends raw extracted text to Groq LLM and asks it to return
    structured JSON matching the BloodParameter schema.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""You are a medical data extraction assistant. Below is raw text extracted from a blood test report PDF. Extract every test parameter into structured JSON.

For each parameter found, extract:
- parameter: the test name (e.g., "Hemoglobin (Hb)")
- result: the numeric result value (e.g., "12.5")
- flag: "Normal" if no flag is shown, otherwise "High", "Low", or "Borderline" exactly as shown
- reference_range: the reference range shown (e.g., "13.0-17.0")
- unit: the unit shown (e.g., "g/dL")

Ignore headers, lab info, doctor names, instrument info, and any non-parameter text.

Return ONLY valid JSON in this exact format, nothing else:
{{"parameters": [{{"parameter": "...", "result": "...", "flag": "...", "reference_range": "...", "unit": "..."}}]}}

Raw text:
{raw_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    return ExtractedReport(**data)


if __name__ == "__main__":
    test_path = "data/test_reports/report_02_drlogy_lipid.pdf"
    text = extract_text_from_pdf(test_path)

    print("\n--- STRUCTURED DATA ---")
    structured = parse_text_to_structured_data(text)
    for param in structured.parameters:
        print(param.model_dump())