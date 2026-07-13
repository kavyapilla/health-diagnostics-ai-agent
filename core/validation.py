from typing import List, Tuple
from core.extraction import BloodParameter


def is_numeric(value: str) -> bool:
    """Check if a result value can be interpreted as a number."""
    try:
        float(value.replace(",", ""))
        return True
    except (ValueError, AttributeError):
        return False


def validate_parameter(param: BloodParameter) -> Tuple[bool, str]:
    """
    Validates a single extracted parameter for basic plausibility.
    Returns (is_valid, reason_if_invalid).
    """
    # Check result is present and non-empty
    if not param.result or not param.result.strip():
        return False, "Missing result value"

    # Check result is numeric (most blood parameters are)
    if not is_numeric(param.result):
        return False, f"Result '{param.result}' is not a valid number"

    # Check flag is one of the expected values
    valid_flags = {"normal", "high", "low", "borderline"}
    if param.flag.lower() not in valid_flags:
        return False, f"Unexpected flag value: '{param.flag}'"

    # Check reference range is present
    if not param.reference_range or not param.reference_range.strip():
        return False, "Missing reference range"

    # Sanity check: result should not be wildly implausible (basic guard, not medical-grade)
    try:
        numeric_result = float(param.result.replace(",", ""))
        if numeric_result < 0:
            return False, f"Negative result value: {numeric_result}"
        if numeric_result > 1_000_000:
            return False, f"Implausibly large result value: {numeric_result}"
    except ValueError:
        pass  # already caught above

    return True, ""


def validate_report(parameters: List[BloodParameter]) -> dict:
    """
    Validates all parameters in a report.
    Returns a dict with valid parameters, invalid parameters (with reasons),
    and summary counts.
    """
    valid_params = []
    invalid_params = []

    for param in parameters:
        is_valid, reason = validate_parameter(param)
        if is_valid:
            valid_params.append(param)
        else:
            invalid_params.append({"parameter": param.model_dump(), "reason": reason})

    return {
        "valid_parameters": valid_params,
        "invalid_parameters": invalid_params,
        "total_extracted": len(parameters),
        "total_valid": len(valid_params),
        "total_invalid": len(invalid_params),
    }


if __name__ == "__main__":
    from core.extraction import extract_text_from_pdf, parse_text_to_structured_data

    test_path = "data/test_reports/report_01_drlogy_cbc.pdf"
    text = extract_text_from_pdf(test_path)
    structured = parse_text_to_structured_data(text)

    result = validate_report(structured.parameters)
    print(f"Total extracted: {result['total_extracted']}")
    print(f"Valid: {result['total_valid']}")
    print(f"Invalid: {result['total_invalid']}")
    if result['invalid_parameters']:
        print("\nInvalid parameters:")
        for item in result['invalid_parameters']:
            print(f"  {item['parameter']['parameter']}: {item['reason']}")