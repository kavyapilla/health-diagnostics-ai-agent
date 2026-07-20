import json
from groq import Groq
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from core.extraction import BloodParameter

load_dotenv()


class SynthesisResult(BaseModel):
    summary: str
    recommendations: List[str]


def synthesize_findings(
    parameters: List[BloodParameter],
    pattern_findings: List[dict],
    context_notes: List[dict],
    age: Optional[int] = None,
    gender: Optional[str] = None
) -> SynthesisResult:
    """
    Combines all extracted parameters, pattern/risk findings, and contextual
    adjustments into one coherent summary and a list of actionable recommendations.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    abnormal_params = [p for p in parameters if p.flag.lower() != "normal"]

    params_text = "\n".join(
        f"- {p.parameter}: {p.result} {p.unit} ({p.flag}), reference: {p.reference_range}"
        for p in parameters
    )

    patterns_text = "\n".join(
        f"- {f['pattern']}: {f['value']} ({f['risk_level']} risk) - {f['explanation']}"
        for f in pattern_findings
    ) or "None identified."

    context_text = "\n".join(
        f"- {n['parameter']}: reclassified from {n['original_flag']} to {n['adjusted_flag']} "
        f"based on {gender} reference range"
        for n in context_notes
    ) or "None."

    user_context = f"Age: {age if age else 'Not provided'}, Gender: {gender if gender else 'Not provided'}"

    prompt = f"""You are a medical information assistant helping a patient understand their blood test report. 
Based on the data below, provide:
1. A clear, coherent, plain-English summary (3-5 sentences) of the overall report — what's normal, what's abnormal, and what it might mean in general terms.
2. A list of 3-6 specific, actionable health recommendations (diet, lifestyle, exercise, follow-up actions) directly tied to the abnormal findings and risk patterns below.

Rules:
- Do NOT provide a diagnosis. Only describe patterns and general implications.
- Always recommend consulting a healthcare professional for any concerning or abnormal results.
- Be specific and actionable in recommendations (not generic advice like "eat healthy" - instead say what kind of foods or actions are relevant to THESE specific findings).
- Keep tone calm, clear, and non-alarming, even for concerning results.

User context: {user_context}

Extracted parameters:
{params_text}

Pattern & risk analysis findings:
{patterns_text}

Contextual (gender-adjusted) reclassifications:
{context_text}

Return ONLY valid JSON in this exact format, nothing else:
{{"summary": "...", "recommendations": ["...", "...", "..."]}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    return SynthesisResult(**data)


if __name__ == "__main__":
    from core.extraction import extract_text_from_pdf, parse_text_to_structured_data
    from core.pattern_analysis import analyze_patterns
    from core.context_analysis import apply_context

    test_path = "data/test_reports/report_02_drlogy_lipid.pdf"
    text = extract_text_from_pdf(test_path)
    structured = parse_text_to_structured_data(text)

    pattern_findings = analyze_patterns(structured.parameters)
    context_notes = apply_context(structured.parameters, age=35, gender="Male")

    result = synthesize_findings(
        structured.parameters,
        pattern_findings,
        context_notes,
        age=35,
        gender="Male"
    )

    print("--- SUMMARY ---")
    print(result.summary)
    print("\n--- RECOMMENDATIONS ---")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"{i}. {rec}")