import os
from google.cloud import storage
from dotenv import load_dotenv
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Initialize Google Cloud Storage client using environment credentials
def initialize_client():
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    return storage.Client()

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the GCS bucket."""
    client = initialize_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def download_from_gcs(bucket_name, blob_name):
    """Downloads a file from GCS and returns it as a BytesIO object."""
    client = initialize_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    data = BytesIO()
    blob.download_to_file(data)
    data.seek(0)  # Rewind the file pointer for reading
    print(f"File {blob_name} downloaded from GCS.")
    return data

def file_exists_in_gcs(bucket_name, blob_name):
    """Checks if a file exists in GCS."""
    client = initialize_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.exists()

def list_files_in_gcs(bucket_name, prefix=None):
    """Lists all files in a given bucket with an optional prefix."""
    client = initialize_client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    return [blob.name for blob in blobs]
