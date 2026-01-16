"""
Dashboard Views
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models.prediction import Prediction
from ..services.image_processor import ImageProcessor
from ..services.inference import InferenceService

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard main page"""
    # Get user's recent predictions
    recent_predictions = Prediction.query.filter_by(user_id=current_user.id)\
        .order_by(Prediction.created_at.desc())\
        .limit(5)\
        .all()
    
    return render_template('dashboard/index.html', recent_predictions=recent_predictions)


@dashboard_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    """Handle image upload and prediction"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Tidak ada file yang diunggah.'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Tidak ada file yang dipilih.'
            }), 400
        
        # Sanitize and validate filename
        original_filename = ImageProcessor.sanitize_filename(file.filename)
        
        if not ImageProcessor.is_allowed_file(original_filename):
            return jsonify({
                'success': False,
                'error': f'Format file tidak didukung. Format yang didukung: {", ".join(ImageProcessor.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Read file content
        file_bytes = file.read()
        
        # Validate file size
        is_valid, message = ImageProcessor.validate_file_size(file_bytes, max_size_mb=10)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Load and preprocess image
        try:
            image = ImageProcessor.load_image(file_bytes)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        # Preprocess for model
        preprocessed = ImageProcessor.preprocess_for_model(image)
        
        # Run inference
        try:
            result = InferenceService.predict(preprocessed)
        except RuntimeError as e:
            current_app.logger.error(f"Inference error: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        
        # Generate filename: [CLASS]_[TIMESTAMP]_[USERNAME].[ext]
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        class_name = result['class'].replace(' ', '')
        username = secure_filename(current_user.username)
        ext = ImageProcessor.get_extension(original_filename) or 'jpg'
        
        # Convert HEIC to JPEG for storage
        if ext.lower() in ['heic', 'heif']:
            ext = 'jpg'
        
        new_filename = f"{class_name}_{timestamp}_{username}.{ext}"
        
        # Save image to upload folder
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, new_filename)
        
        # Determine save format
        save_format = 'JPEG' if ext.lower() in ['jpg', 'jpeg'] else ext.upper()
        if save_format == 'TIF':
            save_format = 'TIFF'
        
        try:
            ImageProcessor.save_image(image, file_path, format=save_format)
        except ValueError as e:
            current_app.logger.error(f"Failed to save image: {str(e)}")
            # Continue even if saving fails - prediction was successful
        
        # Save prediction to database
        prediction = Prediction(
            user_id=current_user.id,
            filename=new_filename,
            original_filename=original_filename,
            result_class=result['class'],
            confidence=result['confidence']
        )
        db.session.add(prediction)
        db.session.commit()
        
        current_app.logger.info(f"Prediction: {result['class']} ({result['confidence']:.2%}) by {current_user.username}")
        
        return jsonify({
            'success': True,
            'result': {
                'class': result['class'],
                'confidence': result['confidence'],
                'confidence_percentage': f"{result['confidence'] * 100:.2f}%",
                'probabilities': {
                    'Normal': f"{result['probabilities']['Normal'] * 100:.2f}%",
                    'Down Syndrome': f"{result['probabilities']['Down Syndrome'] * 100:.2f}%"
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in prediction: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan internal. Silakan coba lagi.'
        }), 500


@dashboard_bp.route('/history')
@login_required
def history():
    """User's prediction history"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    predictions = Prediction.query.filter_by(user_id=current_user.id)\
        .order_by(Prediction.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('dashboard/history.html', predictions=predictions)
