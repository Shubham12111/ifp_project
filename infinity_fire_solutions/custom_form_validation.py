import re
from rest_framework import serializers
from django.contrib.sites.shortcuts import get_current_site

def get_site_url(request):
    current_site = get_current_site(request)
    protocol = 'https' if request.is_secure() else 'http'
    domain = current_site.domain
    site_url = f'{protocol}://{domain}'
    return site_url

def validate_first_name(value):
    # Check if the first name contains only characters or letters with spaces
    if not re.match("^[a-zA-Z ]*$", value):
        raise serializers.ValidationError("First Name can only contain letters and spaces.")

def validate_last_name(value):
    # Check if the first name contains only characters
    if not re.match("^[a-zA-Z ]*$", value):
        raise serializers.ValidationError("First Name can only contain letters and spaces.")

def validate_phone_number(value):
    # Remove any non-digit characters from the input
    cleaned_number = re.sub(r'\D', '', value)

    # Check if the cleaned number has exactly 12 digits
    if len(cleaned_number) != 12:
        raise serializers.ValidationError("Phone number should have 12 digits, including the country code.")

    # Check if the cleaned number starts with the country code +44
    if not cleaned_number.startswith('44'):
        raise serializers.ValidationError("Phone number should start with the country code +44.")

    return value

def validate_uk_postcode(value):
    # Remove any spaces from the input
    cleaned_postcode = value.replace(' ', '').upper()

    # Define a regular expression pattern for a valid UK postcode
    pattern = r'^[A-Z]{1,2}\d{1,2}[A-Z]?\d[A-Z]{2}$'

    # Check if the cleaned postcode matches the pattern
    if not re.match(pattern, cleaned_postcode):
        raise serializers.ValidationError(
            "Invalid UK postcode format. The postcode should have the format: 'SW1A0NY', 'W1J6LE', 'EC2R7DG'."
        )

    return value

def validate_company_name(value):
    # Check if the company name has more than one character
    if len(value) == 3:
        raise serializers.ValidationError("Company name must have more than three character.")
        
        # Check if the company name consists of only spaces and/or tabs
    if value.strip() == "":
        raise serializers.ValidationError("Company name cannot consist of only spaces and/or tabs.")
    
    # Check if the company name is a whole number
    if value.isdigit():
        raise serializers.ValidationError("Company name cannot be a whole number.")
    
    # Check if the company name consists of only special characters
    if re.match("^[&$^#]+$", value):
        raise serializers.ValidationError("Company name cannot consist of only special characters.")

    # Check if the company name contains repeating characters
    if re.search(r'(.)\1{2,}', value):
        raise serializers.ValidationError("Company name cannot contain repeating special characters.")

    return value