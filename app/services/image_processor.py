"""
Image Processing Service
Handles image preprocessing for model inference
"""
import io
import os
from PIL import Image
import numpy as np

# Register HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False


class ImageProcessor:
    """Image processing utilities"""
    
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 'heic', 'heif'}
    TARGET_SIZE = (224, 224)
    
    @classmethod
    def is_allowed_file(cls, filename):
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_extension(cls, filename):
        """Get file extension"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''
    
    @classmethod
    def sanitize_filename(cls, filename):
        """Sanitize filename to remove dangerous characters"""
        # Remove path separators and dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*', '\x00']
        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()
    
    @classmethod
    def load_image(cls, file_path_or_bytes):
        """
        Load image from file path or bytes
        Returns PIL Image in RGB format
        """
        try:
            if isinstance(file_path_or_bytes, (str, os.PathLike)):
                img = Image.open(file_path_or_bytes)
            else:
                img = Image.open(io.BytesIO(file_path_or_bytes))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                if img.mode == 'RGBA':
                    # Handle transparency by creating white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                else:
                    img = img.convert('RGB')
            
            return img
        except Exception as e:
            raise ValueError(f"Gagal memuat gambar: {str(e)}")
    
    @classmethod
    def preprocess_for_model(cls, image, target_size=None):
        """
        Preprocess image for model inference
        - Resize to target size
        - Convert to numpy array
        - Normalize to [0, 1]
        - Add batch dimension
        
        Args:
            image: PIL Image or file path/bytes
            target_size: tuple (width, height), default (224, 224)
        
        Returns:
            numpy array with shape (1, height, width, 3)
        """
        if target_size is None:
            target_size = cls.TARGET_SIZE
        
        # Load image if not already PIL Image
        if not isinstance(image, Image.Image):
            image = cls.load_image(image)
        
        # Resize using high-quality resampling
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        img_array = np.array(image, dtype=np.float32)
        
        # Normalize to [0, 1]
        img_array = img_array / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    @classmethod
    def save_image(cls, image, file_path, format='JPEG', quality=95):
        """
        Save image to file
        
        Args:
            image: PIL Image
            file_path: destination path
            format: output format (JPEG, PNG, etc.)
            quality: JPEG quality (1-100)
        """
        try:
            # Ensure image is in RGB mode for JPEG
            if format.upper() == 'JPEG' and image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Create directory if not exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save with appropriate settings
            if format.upper() == 'JPEG':
                image.save(file_path, format=format, quality=quality, optimize=True)
            elif format.upper() == 'PNG':
                image.save(file_path, format=format, optimize=True)
            else:
                image.save(file_path, format=format)
            
            return True
        except Exception as e:
            raise ValueError(f"Gagal menyimpan gambar: {str(e)}")
    
    @classmethod
    def validate_file_size(cls, file_bytes, max_size_mb=10):
        """
        Validate file size
        
        Args:
            file_bytes: file content as bytes
            max_size_mb: maximum size in megabytes
        
        Returns:
            tuple (is_valid, message)
        """
        file_size = len(file_bytes)
        max_size = max_size_mb * 1024 * 1024
        
        if file_size > max_size:
            return False, f"Ukuran file terlalu besar ({file_size / 1024 / 1024:.2f} MB). Maksimal {max_size_mb} MB."
        
        return True, "OK"
    
    @classmethod
    def get_image_info(cls, image):
        """
        Get image information
        
        Args:
            image: PIL Image
        
        Returns:
            dict with image info
        """
        return {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.width,
            'height': image.height
        }
