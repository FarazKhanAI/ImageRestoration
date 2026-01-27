from flask import Flask, render_template, request, jsonify, send_file, session
import os
import json
import uuid
from pathlib import Path
import tempfile
from werkzeug.utils import secure_filename

from config import Config
from backend.image_processor import ImageProcessor
from backend.utils import ImageUtils
from backend.validators import ImageValidator

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize processors
image_processor = ImageProcessor()
image_utils = ImageUtils()
validator = ImageValidator()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle image upload"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        
        # Validate file
        is_valid, error_message = validator.validate_file(file.stream, file.filename)
        if not is_valid:
            return jsonify({'success': False, 'error': error_message}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = image_utils.generate_unique_filename(original_filename)
        
        # Save original image
        upload_path = Config.RAW_UPLOAD_PATH / unique_filename
        file.save(upload_path)
        
        # Store in session
        session['original_filename'] = unique_filename
        session['original_path'] = str(upload_path)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'message': 'Image uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_image():
    """Process image with enhancements and restoration"""
    try:
        # Check if image file is provided
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Validate file
        is_valid, error_message = validator.validate_file(file.stream, file.filename)
        if not is_valid:
            return jsonify({'success': False, 'error': error_message}), 400
        
        # Generate unique filenames
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        
        original_filename = f"{unique_id}_{original_filename}"
        mask_filename = f"mask_{unique_id}.png"
        processed_filename = f"processed_{unique_id}.jpg"
        
        # Save paths
        original_path = Config.RAW_UPLOAD_PATH / original_filename
        mask_path = Config.MASK_UPLOAD_PATH / mask_filename if 'mask_data' in request.form else None
        processed_path = Config.PROCESSED_PATH / processed_filename
        
        # Save original image
        file.save(original_path)
        
        # Process mask data if provided
        if 'mask_data' in request.form:
            mask_data = json.loads(request.form['mask_data'])
            
            # Load original image to get dimensions
            original_image = image_utils.load_image(str(original_path), mode='color')
            
            # Create mask from coordinates
            mask = image_utils.create_mask_from_coordinates(
                original_image.shape,
                mask_data.get('coordinates', []),
                mask_data.get('brush_size', 20)
            )
            
            # Save mask
            image_utils.save_image(mask, str(mask_path), quality=100)
        
        # Get processing parameters
        parameters = json.loads(request.form.get('parameters', '{}'))
        
        # DEBUG: Log parameter types
        print(f"\n=== DEBUG: Parameters received ===")
        print(f"Raw parameters: {parameters}")
        for key, value in parameters.items():
            print(f"  {key}: {value} (type: {type(value)})")
        
        # Validate parameters
        is_valid, error_message = validator.validate_processing_parameters(parameters)
        if not is_valid:
            print(f"DEBUG: Validation failed: {error_message}")
            return jsonify({'success': False, 'error': error_message}), 400
        
        # DEBUG: Log after validation
        print(f"\n=== DEBUG: After validation ===")
        print(f"Converted parameters: {parameters}")
        for key, value in parameters.items():
            print(f"  {key}: {value} (type: {type(value)})")
        
        # Process image
        result = image_processor.process_image(
            str(original_path),
            str(mask_path) if mask_path else None,
            parameters
        )
        
        if not result['success']:
            print(f"DEBUG: Processing failed: {result.get('error')}")
            return jsonify(result), 500
        
        # Save processed image
        image_utils.save_image(
            result['processed_image'],
            str(processed_path),
            quality=parameters.get('quality', 90)
        )
        
        # Convert images to base64 for display
        original_base64 = image_utils.numpy_to_base64(result['original_image'])
        processed_base64 = image_utils.numpy_to_base64(result['processed_image'])
        
        # Cleanup temporary files
        try:
            if original_path.exists():
                original_path.unlink()
            if mask_path and mask_path.exists():
                mask_path.unlink()
        except:
            pass  # Ignore cleanup errors
        
        return jsonify({
            'success': True,
            'original_image': original_base64,
            'processed_image': processed_base64,
            'metrics': result['metrics'],
            'filename': processed_filename
        })
        
    except Exception as e:
        print(f"DEBUG: Exception in /process: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
def download_image(filename):
    """Download processed image"""
    try:
        file_path = Config.PROCESSED_PATH / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"restored_{filename}"
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/preview', methods=['POST'])
def preview_enhancement():
    """Preview a single enhancement"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        # Get enhancement parameters
        enhancement_type = request.form.get('type')
        value = float(request.form.get('value', 0))
        
        # Load image
        file = request.files['image']
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        file.save(temp_file.name)
        
        # Load image
        image = image_utils.load_image(temp_file.name)
        
        # Apply enhancement
        from backend.enhancement import ImageEnhancer
        enhancer = ImageEnhancer()
        
        enhanced = enhancer.preview_enhancement(image, enhancement_type, value)
        
        # Convert to base64
        enhanced_base64 = image_utils.numpy_to_base64(enhanced)
        
        # Cleanup
        os.unlink(temp_file.name)
        
        return jsonify({
            'success': True,
            'preview_image': enhanced_base64
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    return jsonify({'status': 'healthy', 'service': 'image-restoration'})

@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': 'File too large (max 16MB)'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)