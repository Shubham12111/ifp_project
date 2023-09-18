import re
from django.conf import settings
from bs4 import BeautifulSoup
from rest_framework import serializers
from django.contrib.sites.shortcuts import get_current_site
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os
import pdfkit
from django.template.loader import render_to_string


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

def validate_description(value):
    # Custom validation for the message field to treat <p><br></p> as blank
    soup = BeautifulSoup(value, 'html.parser')
    cleaned_comment = soup.get_text().strip()

    # Check if the cleaned comment consists only of whitespace characters
    if not cleaned_comment:
        raise serializers.ValidationError("Description is required.")

    if all(char.isspace() for char in cleaned_comment):
        raise serializers.ValidationError("Description cannot consist of only spaces and tabs.")

    return value

def action_description(value):
    # Custom validation for the message field to treat <p><br></p> as blank
    soup = BeautifulSoup(value, 'html.parser')
    cleaned_comment = soup.get_text().strip()

    # Check if the cleaned comment consists only of whitespace characters
    if not cleaned_comment:
        raise serializers.ValidationError("Action is required.")

    if all(char.isspace() for char in cleaned_comment):
        raise serializers.ValidationError("Action cannot consist of only spaces and tabs.")

    return value

def validate_rectification_description(value):
    # Custom validation for the message field to treat <p><br></p> as blank
    soup = BeautifulSoup(value, 'html.parser')
    cleaned_comment = soup.get_text().strip()

    # Check if the cleaned comment consists only of whitespace characters
    if not cleaned_comment:
        raise serializers.ValidationError("Rectification description is required.")

    if all(char.isspace() for char in cleaned_comment):
        raise serializers.ValidationError("Rectification description cannot consist of only spaces and tabs.")

    return value


# validate the remarks field in stock/ vendor
def validate_remarks(value):
   soup = BeautifulSoup(value, 'html.parser')
   cleaned_comment = soup.get_text().strip()
   if all(char.isspace() for char in cleaned_comment):
        raise serializers.ValidationError("Remarks cannot consist of only spaces and tabs.")


# Custom validation function for validating file size
def validate_file_size(value):
    """
    Validate the file size is within the allowed limit.

    Parameters:
        value (File): The uploaded file.

    Raises:
        ValidationError: If the file size exceeds the maximum allowed size (5 MB).
    """
    # Maximum file size in bytes (5 MB)
    max_size = 5 * 1024 * 1024

    if value.size > max_size:
        raise ValidationError(_('File size must be up to 5 MB.'))

# Validator for checking the supported file extensions
file_extension_validator = FileExtensionValidator(
    allowed_extensions=settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS,
    message =('Unsupported file extension. Please upload a valid file.'),
)

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
    if re.search(r'([^a-zA-Z0-9])\1{2,}', value):
        raise serializers.ValidationError("Company name cannot contain repeating special characters.")
    
    return value

def no_spaces_or_tabs_validator(value):
    if all(char.isspace() for char in value):
        raise ValidationError("Cannot consist of only spaces and/or tabs.")



def validate_name(value):
         # Check if the name is a whole number
         if value.isdigit():
             raise serializers.ValidationError("Name cannot be a number.")

         # Check if the name consists of only spaces and/or tabs
         if value.strip() == "":
             raise serializers.ValidationError("Name cannot consist of only spaces and/or tabs.")

         # Check if the name consists of only special characters
         if re.match(r'^[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?]*$', value):
             raise serializers.ValidationError("Name cannot consist of only special characters.")
         return value


# pDF SETTINGS
pdf_options = {
        'page-size': 'A4',  # You can change this to 'A4' or custom size
        'margin-top': '10mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
    }

def save_pdf_from_html(context, file_name, content_html):
    """
    Save the PDF file from the HTML content.
    Args:
        context (dict): Context data for rendering the HTML template.
        file_name (str): Name of the PDF file.
    Returns:
        Output file path or None.
    """
    output_file = None
    local_folder = '/tmp'

    if local_folder:
        try:
            os.makedirs(local_folder, exist_ok=True)
            output_file = os.path.join(local_folder, file_name)
            # get the html text from the tmplate
            html_content = render_to_string(content_html, context)

            # create the PDF file for the invoice
            pdfkit.from_string(html_content, output_file, options=pdf_options)
            
        except Exception as e:
            # Handle any exceptions that occur during PDF generation
            print("error")

    return output_file
