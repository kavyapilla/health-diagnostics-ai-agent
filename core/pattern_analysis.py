from typing import List, Dict
from core.extraction import BloodParameter


def get_param_value(parameters: List[BloodParameter], name: str) -> float | None:
    """
    Finds a parameter by name (case-insensitive partial match) and returns its numeric value.
    Returns None if not found or not numeric.
    """
    for p in parameters:
        if name.lower() in p.parameter.lower():
            try:
                return float(p.result.replace(",", ""))
            except (ValueError, AttributeError):
                return None
    return None


def analyze_lipid_patterns(parameters: List[BloodParameter]) -> List[Dict]:
    """
    Analyzes lipid panel parameters for cardiovascular risk patterns.
    Returns a list of findings with risk level and explanation.
    """
    findings = []

    total_chol = get_param_value(parameters, "Cholesterol Total")
    hdl = get_param_value(parameters, "HDL Cholesterol")
    ldl = get_param_value(parameters, "LDL Cholesterol")
    triglycerides = get_param_value(parameters, "Triglycerides")

    # Total Cholesterol / HDL Ratio - a well-established cardiovascular risk indicator
    if total_chol is not None and hdl is not None and hdl > 0:
        tc_hdl_ratio = round(total_chol / hdl, 2)
        if tc_hdl_ratio < 3.5:
            risk = "Low"
        elif tc_hdl_ratio < 5.0:
            risk = "Moderate"
        else:
            risk = "High"
        findings.append({
            "pattern": "Total Cholesterol / HDL Ratio",
            "value": tc_hdl_ratio,
            "risk_level": risk,
            "explanation": f"A ratio of {tc_hdl_ratio} indicates {risk.lower()} cardiovascular risk. "
                            f"Ratios below 3.5 are considered optimal; above 5.0 indicates elevated risk."
        })

    # LDL / HDL Ratio - another standard cardiovascular risk marker
    if ldl is not None and hdl is not None and hdl > 0:
        ldl_hdl_ratio = round(ldl / hdl, 2)
        if ldl_hdl_ratio < 2.5:
            risk = "Low"
        elif ldl_hdl_ratio < 4.0:
            risk = "Moderate"
        else:
            risk = "High"
        findings.append({
            "pattern": "LDL / HDL Ratio",
            "value": ldl_hdl_ratio,
            "risk_level": risk,
            "explanation": f"A ratio of {ldl_hdl_ratio} indicates {risk.lower()} cardiovascular risk."
        })

    # Triglyceride / HDL Ratio - associated with insulin resistance risk
    if triglycerides is not None and hdl is not None and hdl > 0:
        tg_hdl_ratio = round(triglycerides / hdl, 2)
        if tg_hdl_ratio < 2.0:
            risk = "Low"
        elif tg_hdl_ratio < 4.0:
            risk = "Moderate"
        else:
            risk = "High"
        findings.append({
            "pattern": "Triglyceride / HDL Ratio",
            "value": tg_hdl_ratio,
            "risk_level": risk,
            "explanation": f"A ratio of {tg_hdl_ratio} may indicate {risk.lower()} risk of insulin resistance."
        })

    return findings


def analyze_cbc_patterns(parameters: List[BloodParameter]) -> List[Dict]:
    """
    Analyzes CBC parameters for common patterns (e.g., anemia indicators).
    """
    findings = []

    hemoglobin = get_param_value(parameters, "Hemoglobin")
    mcv = get_param_value(parameters, "Mean Corpuscular Volume")

    # Basic anemia pattern: low hemoglobin + low/normal/high MCV suggests different anemia types
    if hemoglobin is not None and hemoglobin < 13.0:  # simplified threshold, not gender-adjusted
        if mcv is not None:
            if mcv < 80:
                anemia_type = "microcytic (possibly iron-deficiency related)"
            elif mcv > 100:
                anemia_type = "macrocytic (possibly B12/folate related)"
            else:
                anemia_type = "normocytic"
            findings.append({
                "pattern": "Anemia Indicator",
                "value": f"Hb: {hemoglobin}, MCV: {mcv}",
                "risk_level": "Moderate",
                "explanation": f"Low hemoglobin with this MCV pattern suggests possible {anemia_type} anemia. "
                                f"Further clinical evaluation is recommended."
            })

    return findings


def analyze_patterns(parameters: List[BloodParameter]) -> List[Dict]:
    """
    Runs all applicable pattern analyses based on which parameters are present.
    """
    all_findings = []
    all_findings.extend(analyze_lipid_patterns(parameters))
    all_findings.extend(analyze_cbc_patterns(parameters))
    return all_findings


if __name__ == "__main__":
    from core.extraction import extract_text_from_pdf, parse_text_to_structured_data

    test_path = "data/test_reports/report_02_drlogy_lipid.pdf"
    text = extract_text_from_pdf(test_path)
    structured = parse_text_to_structured_data(text)

    findings = analyze_patterns(structured.parameters)
    print(f"Found {len(findings)} pattern(s):\n")
    for f in findings:
        print(f"[{f['risk_level']}] {f['pattern']}: {f['value']}")
        print(f"  {f['explanation']}\n")