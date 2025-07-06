from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


# Create reusable Presidio engine instances
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def scrub_text(text_to_scrub: str) -> str:
    """
    Analyze text for PII entities and anonymize them with placeholder values.
    
    This function uses Microsoft Presidio to detect various types of personally
    identifiable information (PII) such as emails, phone numbers, credit cards,
    names, locations, etc., and replaces them with descriptive placeholders.
    
    Args:
        text_to_scrub: The input text that may contain PII.
        
    Returns:
        str: The anonymized text with PII replaced by placeholders.
        
    Example:
        >>> scrub_text("My email is john.doe@company.com and phone is 555-123-4567")
        "My email is <EMAIL_ADDRESS> and phone is <PHONE_NUMBER>"
    """
    if not text_to_scrub or not text_to_scrub.strip():
        return text_to_scrub
    
    try:
        # Analyze the text to find PII entities
        analyzer_results = analyzer.analyze(
            text=text_to_scrub,
            language='en'
        )
        
        # Configure anonymization operators for different entity types
        # This creates human-readable placeholders instead of random values
        operators = {
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL_ADDRESS>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE_NUMBER>"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSON_NAME>"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
            "IBAN_CODE": OperatorConfig("replace", {"new_value": "<IBAN_CODE>"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "<SSN>"}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "<IP_ADDRESS>"}),
            "URL": OperatorConfig("replace", {"new_value": "<URL>"}),
            "US_DRIVER_LICENSE": OperatorConfig("replace", {"new_value": "<DRIVER_LICENSE>"}),
            "US_PASSPORT": OperatorConfig("replace", {"new_value": "<PASSPORT>"}),
            "DATE_TIME": OperatorConfig("replace", {"new_value": "<DATE_TIME>"}),
            "MEDICAL_LICENSE": OperatorConfig("replace", {"new_value": "<MEDICAL_LICENSE>"}),
            "NRP": OperatorConfig("replace", {"new_value": "<NATIONAL_ID>"}),
        }
        
        # Anonymize the text using the analyzer results and our operators
        anonymized_result = anonymizer.anonymize(
            text=text_to_scrub,
            analyzer_results=analyzer_results,
            operators=operators
        )
        
        return anonymized_result.text
        
    except Exception as e:
        # Log the error in production, but don't block the request
        print(f"DLP scanning error: {e}")
        # Return original text if DLP fails to avoid breaking the service
        return text_to_scrub