import boto3
from botocore import exceptions

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.template.loader import render_to_string
from authentication.models import User

class Email:
    """
    This class handles the sending of emails using Amazon SES.
    """

    from_email = settings.FROM_EMAIL

    def __init__(self):
        """
        Initializes the Email instance with the necessary configurations for Amazon SES.
        """
        self.client = boto3.client('ses',region_name=settings.AWS_REGION,)

   
    def get_html_content(self, template_name: str, context: dict):
        """
        Renders the HTML template with the given context and returns the HTML content.

        Parameters:
        - template_name: The name of the email template.
        - context: The context variables to be used in the email template.

        Returns:
        - The HTML content of the email.
        """

        html_content = render_to_string(template_name, context)
        return html_content

    def send_mail(self, to_email: str, template_name: str, context: dict, subject):

        """
        Sends the email using Amazon SES.

        Parameters:
        - to_email: The email address of the recipient.
        - template_name: The name of the email template.
        - context: The context variables to be used in the email template.

        Raises:
        - ClientError: If there is an error while sending the email.
        - Exception: For general errors while sending the email.
        """
        html_content = self.get_html_content(template_name, context)

        message = {
            'Subject': {'Data': subject},
            'Body': {
                'Html': {'Data': html_content},
            }
        }

        try:
            response = self.client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message=message
            )
            print("Email sent:", response['MessageId'])

        except exceptions.ClientError as e:
            print(f"Error sending email: {e.response['Error']['Message']}")
            raise  # Re-raise the exception to handle it at a higher level

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise  # Re-raise the exception to handle it at a higher level