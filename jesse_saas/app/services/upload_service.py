import os
import cloudinary
import cloudinary.uploader
from flask import current_app
from werkzeug.utils import secure_filename
from datetime import datetime

class UploadService:
    @staticmethod
    def _is_cloudinary_configured():
        return all([
            current_app.config.get('CLOUDINARY_CLOUD_NAME'),
            current_app.config.get('CLOUDINARY_API_KEY'),
            current_app.config.get('CLOUDINARY_API_SECRET')
        ])

    @staticmethod
    def _init_cloudinary():
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )

    @staticmethod
    def upload(file, folder='uploads', public_id_prefix=''):
        """
        Uploads a file to Cloudinary or falls back to local storage.
        Returns the public URL (or local path fallback) of the uploaded file.
        """
        if not file or file.filename == '':
            return None

        # Prepare filename
        filename = secure_filename(file.filename)
        
        # 1. Cloudinary Upload (If Configured)
        if UploadService._is_cloudinary_configured():
            try:
                UploadService._init_cloudinary()
                
                # Cloudinary allows organizing by folders and adding a prefix
                # We use timestamp to ensure uniqueness just in case
                public_id = f"{folder}/{public_id_prefix}_{datetime.now().timestamp()}_{filename.split('.')[0]}"
                
                # Direct Upload
                response = cloudinary.uploader.upload(
                    file,
                    public_id=public_id,
                    resource_type="auto" # Auto-detect image/video
                )
                
                # Return SSL URL
                return response.get('secure_url')
                
            except Exception as e:
                print(f"Cloudinary Upload Error: {e}")
                # Fallback to local? Or fail? 
                # Better to fallback for now if it's a temp issue, 
                # but for Vercel this fallback is useless.
                # Let's try local fallback as safety net for dev.
                pass

        # 2. Local Fallback (Dev / No Cloudinary)
        try:
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Timestamp to avoid collisions
            saved_filename = f"{public_id_prefix}_{datetime.now().timestamp()}_{filename}"
            file_path = os.path.join(upload_dir, saved_filename)
            
            # Reset file pointer if it was read by Cloudinary attempt
            file.seek(0)
            file.save(file_path)
            
            # For local, we need to return a path relative to the app so url_for can use it
            # But the existing logic uses a special route.
            # Let's start by identifying if we can return a usable reference.
            # Admin Routes currently assume a filename that can be passed to 'uploaded_file'.
            
            # If we return a full URL here, the calling code needs to handle it.
            # Strategy: Return "local:{folder}/{filename}" marker or just filename?
            
            # Hack for backward compat:
            # If local, we return just the filename so existing 'url_for' logic works?
            # Or we standardize EVERYTHING to be a full URL.
            
            # Let's standardize to returning the Filename for local, 
            # but callers need to know if it's a URL or a filename.
            
            # Actually, let's make this service return a dict or object?
            # Or just return the string. If it starts with http, it's remote.
            
            return f"{folder}/{saved_filename}" # We'll need to adjust how this is served.
            
        except Exception as e:
            print(f"Local Upload Error: {e}")
            return None

    @staticmethod
    def is_remote_url(path):
        """Helper to check if a stored string is a full URL or local path."""
        if not path: return False
        return path.startswith('http://') or path.startswith('https://')
