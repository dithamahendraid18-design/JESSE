import os
import cloudinary
import cloudinary.uploader
import re
from flask import current_app, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}

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
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def upload(file, folder='uploads', public_id_prefix=''):
        """
        Uploads a file to Cloudinary or falls back to local storage.
        Returns the public URL (or local path fallback) of the uploaded file.
        Enforces image validation.
        """
        if not file or file.filename == '':
            return None

        if not UploadService.allowed_file(file.filename):
            print(f"Security: Blocked upload of {file.filename} (Invalid Extension)")
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
                    resource_type="image" # Force image type for security
                )
                
                # Return SSL URL
                return response.get('secure_url')
                
            except Exception as e:
                print(f"Cloudinary Upload Error: {e}")
                # Fallback to local? Or fail? 
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
            
            return f"{folder}/{saved_filename}" # We'll need to adjust how this is served.
            
        except Exception as e:
            print(f"Local Upload Error: {e}")
            return None

    @staticmethod
    def is_remote_url(path):
        """Helper to check if a stored string is a full URL or local path."""
        if not path: return False
        return path.startswith('http://') or path.startswith('https://')

    @staticmethod
    def resolve_url(filename, width=None):
        """
        Generates the final URL for an image, handling both Cloudinary transforms
        and local standard routes.
        This replaces the complex logic in __init__.py.
        """
        if not filename: return None

        # Remote / Cloudinary
        if UploadService.is_remote_url(filename):
            # Optimize Cloudinary URLs
            if 'cloudinary.com' in filename and '/upload/' in filename:
                # Default transformations: Auto format (WebP/AVIF), Auto Quality
                transforms = ['f_auto', 'q_auto']
                
                if width:
                    transforms.append(f'w_{width}')
                    transforms.append('c_limit') # Resize but maintain aspect ratio (don't crop)
                
                transform_str = ','.join(transforms)
                
                # Inject transformations after /upload/
                return re.sub(r'(/upload/)', f'\\1{transform_str}/', filename, count=1)
            
            return filename

        # Local File
        # Assuming filename is "folder/file.ext"
        return url_for('uploaded_file', filename=filename)

