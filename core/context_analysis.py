from typing import List, Dict, Optional
from core.extraction import BloodParameter


# Reference ranges that commonly differ by gender
# Format: {parameter_keyword: {"male": (low, high), "female": (low, high)}}
GENDER_ADJUSTED_RANGES = {
    "hemoglobin": {
        "male": (13.5, 17.5),
        "female": (12.0, 15.5),
    },
    "total rbc count": {
        "male": (4.7, 6.1),
        "female": (4.2, 5.4),
    },
    "hematocrit": {
        "male": (38.8, 50.0),
        "female": (34.9, 44.5),
    },
}


def apply_context(
    parameters: List[BloodParameter],
    age: Optional[int] = None,
    gender: Optional[str] = None
) -> List[Dict]:
    """
    Re-evaluates parameters using gender-adjusted reference ranges where applicable.
    Returns a list of context-adjusted notes (only for parameters where context changes the interpretation).
    """
    notes = []

    if not gender:
        return notes  # no context provided, nothing to adjust

    gender_key = gender.strip().lower()
    if gender_key not in ("male", "female"):
        return notes

    for param in parameters:
        param_name_lower = param.parameter.lower()

        for keyword, ranges in GENDER_ADJUSTED_RANGES.items():
            if keyword in param_name_lower:
                try:
                    value = float(param.result.replace(",", ""))
                except (ValueError, AttributeError):
                    continue

                low, high = ranges[gender_key]

                if value < low:
                    adjusted_flag = "Low"
                elif value > high:
                    adjusted_flag = "High"
                else:
                    adjusted_flag = "Normal"

                # Only add a note if the gender-adjusted flag differs from the original flag
                if adjusted_flag.lower() != param.flag.lower():
                    notes.append({
                        "parameter": param.parameter,
                        "original_flag": param.flag,
                        "adjusted_flag": adjusted_flag,
                        "gender_adjusted_range": f"{low} - {high}",
                        "explanation": f"Using {gender_key}-specific reference range ({low}-{high}), "
                                       f"this result is more accurately classified as '{adjusted_flag}' "
                                       f"rather than the report's general '{param.flag}' flag."
                    })
                break  # matched this parameter, no need to check other keywords

    return notes


if __name__ == "__main__":
    from core.extraction import extract_text_from_pdf, parse_text_to_structured_data

    test_path = "data/test_reports/report_01_drlogy_cbc.pdf"
    text = extract_text_from_pdf(test_path)
    structured = parse_text_to_structured_data(text)

    # Test with female context (the report used a general/male-leaning range where Hb 12.5 was flagged "Low")
    print("--- Testing with gender = Female ---")
    notes = apply_context(structured.parameters, age=28, gender="Female")
    if notes:
        for n in notes:
            print(f"{n['parameter']}: {n['original_flag']} -> {n['adjusted_flag']}")
            print(f"  {n['explanation']}\n")
    else:
        print("No context-based adjustments needed.")

    print("--- Testing with gender = Male ---")
    notes = apply_context(structured.parameters, age=28, gender="Male")
    if notes:
        for n in notes:
            print(f"{n['parameter']}: {n['original_flag']} -> {n['adjusted_flag']}")
            print(f"  {n['explanation']}\n")
    else:
        print("No context-based adjustments needed.")