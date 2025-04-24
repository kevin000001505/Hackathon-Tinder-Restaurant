import os
import time
import uuid
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
import backend.config as config


def initialize_firebase():
    """Initialize Firebase app with credentials"""
    # Path to your Firebase service account key JSON file
    cred_path = config.FIREBASE_ACCOUNT_KEY

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(
            cred, {"storageBucket": "your-firebase-project-id.appspot.com"}
        )

    return storage.bucket()


def upload_image(image_path, image_id, folder_name=None):
    """
    Upload an image to Firebase Storage and return a temporary URL valid for 30 minutes

    Args:
        image_path (str): Path to the image file
        image_id (str): The ID for this image
        folder_name (str, optional): Folder to upload image to in storage

    Returns:
        dict: Image info including temporary public URL
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Initialize Firebase bucket
    bucket = initialize_firebase()

    # Generate a filename using the provided ID
    filename = os.path.basename(image_path)
    file_extension = os.path.splitext(filename)[1]
    unique_filename = f"{image_id}{file_extension}"

    # Set the destination path in Firebase storage
    destination_path = unique_filename
    if folder_name:
        destination_path = f"{folder_name}/{unique_filename}"

    # Upload the file
    blob = bucket.blob(destination_path)
    blob.upload_from_filename(image_path)

    # Generate a signed URL that expires in 30 minutes
    expiration_time = datetime.now() + timedelta(minutes=30)
    url = blob.generate_signed_url(
        version="v4", expiration=expiration_time, method="GET"
    )

    return {
        "id": image_id,
        "filename": unique_filename,
        "storage_path": destination_path,
        "public_url": url,
        "expires_at": expiration_time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def bulk_upload_images_with_ids(image_info_list, folder_name=None):
    """
    Upload multiple images with their IDs

    Args:
        image_info_list (list): List of dicts with 'path' and 'id' for each image
            Example: [{'path': '/path/to/image1.jpg', 'id': 'img001'}, ...]
        folder_name (str, optional): Folder in Firebase to upload to

    Returns:
        dict: Dictionary mapping image IDs to their info with URLs
    """
    results_dict = {}

    for image_info in image_info_list:
        image_path = image_info["path"]
        image_id = image_info["id"]

        try:
            result = upload_image(image_path, image_id, folder_name)
            results_dict[image_id] = result
            print(f"Successfully uploaded image with ID: {image_id}")
        except Exception as e:
            print(f"Error uploading image with ID {image_id}: {str(e)}")
            # Add error info to results
            results_dict[image_id] = {
                "id": image_id,
                "error": str(e),
                "status": "failed",
            }

    return results_dict


def get_urls_dict(results_dict):
    """
    Extract just the ID-to-URL mapping from the results dictionary

    Args:
        results_dict (dict): The full results from bulk_upload_images_with_ids

    Returns:
        dict: Simple dictionary mapping image IDs to their URLs
    """
    urls_dict = {}
    for image_id, image_info in results_dict.items():
        if "public_url" in image_info:  # Only add successful uploads
            urls_dict[image_id] = image_info["public_url"]

    return urls_dict


def main():
    """Example usage of the functions"""
    # Example 1: Upload a single image with ID
    try:
        image_id = "product_123"
        result = upload_image("path/to/your/image.jpg", image_id, "temp_images")
        print(f"Image uploaded successfully with ID: {image_id}")
        print(f"Temporary URL (expires in 30 mins): {result['public_url']}")
        print(f"Expires at: {result['expires_at']}")

        # Create a simple ID-to-URL dictionary
        urls_dict = {image_id: result["public_url"]}
        print(f"URLs Dictionary: {urls_dict}")
    except Exception as e:
        print(f"Error uploading image: {str(e)}")

    # Example 2: Upload multiple images with IDs
    try:
        # List of images with their respective IDs
        image_info_list = [
            {"path": "path/to/image1.jpg", "id": "product_001"},
            {"path": "path/to/image2.png", "id": "product_002"},
            {"path": "path/to/image3.jpg", "id": "banner_001"},
        ]

        results_dict = bulk_upload_images_with_ids(image_info_list, "products")

        # Create a simple dictionary with just IDs and URLs
        urls_dict = get_urls_dict(results_dict)

        print("\nID to URL Dictionary:")
        for image_id, url in urls_dict.items():
            print(f"{image_id}: {url}")

        # This urls_dict can now be used in your application
        print("\nTotal images successfully uploaded:", len(urls_dict))

    except Exception as e:
        print(f"Error during bulk upload: {str(e)}")


if __name__ == "__main__":
    main()
