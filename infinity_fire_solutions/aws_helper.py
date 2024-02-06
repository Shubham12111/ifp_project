from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

# Set up the S3 client with your AWS credentials and region
s3_client = boto3.client('s3', region_name='eu-west-2')

# Function to upload a file to Amazon S3
def upload_signature_to_s3(file_name, file_path, s3_folder=''):
    try:
        s3_key = f"{s3_folder}/{file_name}"
        s3_client.upload_file(file_path, settings.AWS_BUCKET_NAME, s3_key)
        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False




def upload_file_to_s3(unique_filename, file_path, s3_folder=''):
    """
    Uploads a file to Amazon S3.

    Parameters:
        unique_filename (str): The unique filename to be used for the uploaded file.
        file_path: The file-like object to be uploaded.
        s3_folder (str, optional): The S3 folder in which to store the file. Default is an empty string.

    Returns:
        str: The URL of the uploaded file on S3.
    """
    # Upload the file to S3
    
    s3_key = f"{s3_folder}/{unique_filename}"
    s3_client.upload_fileobj(file_path, settings.AWS_BUCKET_NAME, s3_key)

    # Get the link to the uploaded file
    s3_url = f"https://{settings.AWS_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

    return s3_url

def generate_presigned_url(s3_key, expiration=3600):
    """
    Generates a pre-signed URL for downloading a file from Amazon S3.

    Parameters:
        s3_key (str): The S3 key of the file to be downloaded.
        expiration (int, optional): The expiration time of the pre-signed URL in seconds. Default is 3600 (1 hour).

    Returns:
        str: The pre-signed URL for downloading the file from S3.
    """
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_BUCKET_NAME,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
    except ClientError as e:
        # Handle the error
        print(e)
        return None

    return response

def fetch_file_from_s3(unique_filename, s3_folder=''):
    """
    Fetches a file from Amazon S3 and keeps it in memory.

    Parameters:
        bucket_name (str): The name of the S3 bucket.
        key (str): The key of the file in the S3 bucket.

    Returns:
        BytesIO: A BytesIO object containing the file content.
    """
    try:
        s3_key = f"{s3_folder}/{unique_filename}"

        # Download the file from S3
        file_object = BytesIO()
        s3_client.download_fileobj(settings.AWS_BUCKET_NAME, s3_key, file_object)
        file_object.seek(0)  # Reset the file pointer to the beginning
        return file_object
    
    except Exception as e:
        return None


def delete_file_from_s3(file_key, s3_folder=''):
    """
    Delete a file from AWS S3.

    Args:
        file_key (str): The key of the file to be deleted in the S3 bucket.

    Returns:
        bool: True if the file was successfully deleted, False otherwise.
    """
    s3_key = f"{s3_folder}/{file_key}"
    try:
        # Delete the file from S3
        s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=s3_key)
        return True
    except Exception as e:
        # Log or handle the exception appropriately
        return False