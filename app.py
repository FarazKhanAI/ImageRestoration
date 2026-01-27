from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import uuid
from pathlib import Path
import numpy as np
import traceback

from config import Config
from backend.image_processor import RobustImageProcessor
from backend.utils import ImageUtils

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Ensure directories exist
Config.init_app(app)

# Initialize processors
processor = RobustImageProcessor()
utils = ImageUtils()

@app.route('/')
def index():
    return render_template('index.html')

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

@app.route('/process', methods=['POST'])
def process_image():
    """
    Main processing endpoint
    """
    print("\n" + "="*60)
    print("RECEIVED PROCESS REQUEST")
    print("="*60)
    
    try:
        # 1. Check for image
        if 'image' not in request.files:
            print("ERROR: No image in request")
            return jsonify({'success': False, 'error': 'No image file'}), 400
        
        file = request.files['image']
        if file.filename == '':
            print("ERROR: Empty filename")
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        
        # 2. Generate unique filenames
        unique_id = str(uuid.uuid4())[:8]
        original_filename = f"input_{unique_id}.jpg"
        processed_filename = f"output_{unique_id}.jpg"
        
        original_path = Config.RAW_UPLOAD_PATH / original_filename
        processed_path = Config.PROCESSED_PATH / processed_filename
        
        print(f"File ID: {unique_id}")
        print(f"Original: {original_path}")
        print(f"Processed: {processed_path}")
        
        # 3. Save uploaded file
        file.save(original_path)
        print(f"File saved: {original_path.exists()}")
        



        # 4. Parse mask data
        mask_data = None
        mask_path = None
        if 'mask_data' in request.form and request.form['mask_data']:
            try:
                mask_json = request.form['mask_data']
                mask_data = json.loads(mask_json)
                
                print(f"Mask data received:")
                print(f"  Points: {len(mask_data.get('coordinates', []))}")
                print(f"  Brush size: {mask_data.get('brush_size', 20)}")
                
                # Debug: print first few coordinates
                coords = mask_data.get('coordinates', [])
                if coords:
                    for i, coord in enumerate(coords[:3]):
                        print(f"  Coord {i}: {coord}")
                    
                    # Create mask path with your desired location
                    mask_filename = f"mask_{unique_id}.png"
                    mask_path = Config.MASK_UPLOAD_PATH / mask_filename
                    
                    print(f"Mask will be saved to: {mask_path}")
                
            except Exception as e:
                print(f"Error parsing mask data: {e}")
                mask_data = None
        








        # 5. Parse parameters
        parameters = {}
        if 'parameters' in request.form and request.form['parameters']:
            try:
                parameters = json.loads(request.form['parameters'])
                print(f"Parameters: {parameters}")
            except:
                pass
        
        # 6. Process image
        print("\nStarting image processing...")
        result = processor.process(str(original_path), mask_data)
        
        if not result['success']:
            print(f"Processing failed: {result.get('error')}")
            return jsonify(result), 500
        
        print("Processing successful!")
        
        # 7. Save result
        utils.save_image(result['processed_image'], str(processed_path), quality=95)
        print(f"Result saved to: {processed_path}")
        
        # 8. Convert to base64 for response
        original_base64 = utils.numpy_to_base64(result['original_image'])
        processed_base64 = utils.numpy_to_base64(result['processed_image'])
        
        # 9. Prepare response - Convert all numpy types to Python types
        response_data = {
            'success': True,
            'original_image': original_base64,
            'processed_image': processed_base64,
            'metrics': convert_numpy_types(result['metrics']),
            'filename': processed_filename,
            'mask_used': bool(result.get('mask_created', False))  # Convert numpy bool to Python bool
        }
        
        print(f"Response prepared. Mask used: {result.get('mask_created', False)}")
        print("="*60 + "\n")
        
        # 10. Cleanup
        try:
            if original_path.exists():
                original_path.unlink()
        except:
            pass
        
        # Convert response data to ensure JSON serializable
        response_data = convert_numpy_types(response_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

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

@app.route('/test-mask', methods=['POST'])
def test_mask():
    """Test endpoint for mask creation"""
    try:
        data = request.json
        coordinates = data.get('coordinates', [])
        brush_size = data.get('brush_size', 20)
        
        # Create a test mask
        from backend.scratch_removal import AdvancedInpainter
        inpainter = AdvancedInpainter()
        
        # Test mask on 400x400 image
        test_shape = (400, 400)
        mask = inpainter.create_precise_mask(test_shape, coordinates, brush_size)
        
        # Save test mask
        test_path = Config.PROCESSED_PATH / "test_mask.png"
        utils.save_image(mask, str(test_path), quality=100)
        
        return jsonify({
            'success': True,
            'mask_pixels': int(np.sum(mask > 0)),
            'mask_path': str(test_path)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)