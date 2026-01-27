from flask import Flask, render_template, request, jsonify, send_file, session
import os
import json
import uuid
from pathlib import Path
import tempfile
from werkzeug.utils import secure_filename
import traceback

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

# Debug mode
DEBUG = True

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
        file.stream.seek(0)
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
        if DEBUG:
            traceback.print_exc()
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
        file.stream.seek(0)
        is_valid, error_message = validator.validate_file(file.stream, file.filename)
        if not is_valid:
            return jsonify({'success': False, 'error': error_message}), 400
        
        # Generate unique filenames
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        
        original_filename = f"{unique_id}_{original_filename}"
        mask_filename = f"mask_{unique_id}.png"
        processed_filename = f"processed_{unique_id}.jpg"
        
        # Create paths
        original_path = Config.RAW_UPLOAD_PATH / original_filename
        mask_path = Config.MASK_UPLOAD_PATH / mask_filename
        processed_path = Config.PROCESSED_PATH / processed_filename
        
        # Ensure mask directory exists
        Config.MASK_UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
        
        # Save original image
        file.save(original_path)
        
        # Process mask data if provided
        mask_coordinates = None
        if 'mask_data' in request.form:
            mask_data = request.form['mask_data']
            if mask_data and mask_data != 'undefined':
                try:
                    mask_data = json.loads(mask_data)
                    
                    # Load original image to get dimensions
                    original_image = image_utils.load_image(str(original_path), mode='color')
                    
                    # Get brush size from parameters
                    parameters = json.loads(request.form.get('parameters', '{}'))
                    brush_size = parameters.get('brush_size', 20)
                    
                    # Create mask from coordinates
                    coordinates = mask_data.get('coordinates', [])
                    mask_coordinates = coordinates  # Save for debugging
                    
                    if coordinates:
                        mask = image_utils.create_advanced_mask(
                            original_image.shape,
                            coordinates,
                            brush_size,
                            feather=True
                        )
                        
                        # Save mask with metadata
                        image_utils.save_mask_with_metadata(
                            mask, str(mask_path), 
                            coordinates, brush_size
                        )
                        
                        if DEBUG:
                            print(f"Mask saved to: {mask_path}")
                            print(f"Mask area: {np.sum(mask > 0)} pixels")
                    else:
                        mask_path = None
                except json.JSONDecodeError:
                    mask_path = None
                except Exception as e:
                    if DEBUG:
                        print(f"Mask creation error: {e}")
                    mask_path = None
        else:
            mask_path = None
        
        # Get processing parameters
        parameters = json.loads(request.form.get('parameters', '{}'))
        
        if DEBUG:
            print(f"\n=== Processing Parameters ===")
            print(f"Original: {original_path}")
            print(f"Mask: {mask_path}")
            print(f"Parameters: {parameters}")
        
        # Validate parameters
        is_valid, error_message = validator.validate_processing_parameters(parameters)
        if not is_valid:
            return jsonify({'success': False, 'error': error_message}), 400
        
        # Process image
        result = image_processor.process_image(
            str(original_path),
            str(mask_path) if mask_path and mask_path.exists() else None,
            parameters
        )
        
        if not result['success']:
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
        
        # Prepare response
        response_data = {
            'success': True,
            'original_image': original_base64,
            'processed_image': processed_base64,
            'metrics': result['metrics'],
            'filename': processed_filename,
            'mask_saved': mask_path is not None and mask_path.exists()
        }
        
        # Add debug info if enabled
        if DEBUG:
            response_data['debug'] = {
                'original_path': str(original_path),
                'mask_path': str(mask_path) if mask_path else None,
                'mask_coordinates_count': len(mask_coordinates) if mask_coordinates else 0,
                'parameters_used': parameters
            }
        
        # Cleanup temporary files (keep for debugging)
        if not DEBUG:
            try:
                if original_path.exists():
                    original_path.unlink()
                if mask_path and mask_path.exists():
                    mask_path.unlink()
            except:
                pass
        
        return jsonify(response_data)
        
    except Exception as e:
        if DEBUG:
            traceback.print_exc()
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
        
        enhanced = image_processor.preview_enhancement(image, enhancement_type, value)
        
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
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'image-restoration',
        'directories': {
            'raw': str(Config.RAW_UPLOAD_PATH),
            'masks': str(Config.MASK_UPLOAD_PATH),
            'processed': str(Config.PROCESSED_PATH)
        }
    })

@app.route('/debug/masks', methods=['GET'])
def list_masks():
    """Debug endpoint to list saved masks"""
    if not DEBUG:
        return jsonify({'error': 'Debug mode disabled'}), 403
    
    masks = []
    for mask_file in Config.MASK_UPLOAD_PATH.glob('*.png'):
        masks.append({
            'name': mask_file.name,
            'size': mask_file.stat().st_size,
            'modified': mask_file.stat().st_mtime
        })
    
    return jsonify({
        'success': True,
        'count': len(masks),
        'masks': masks
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': 'File too large (max 16MB)'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    if DEBUG:
        traceback.print_exc()
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=5000)