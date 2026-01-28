from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, send_from_directory
import os
import json
import uuid
from pathlib import Path
import numpy as np
import traceback
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config
from backend.image_processor import RobustImageProcessor
from backend.utils import ImageUtils

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get('SECRET_KEY')

# Ensure directories exist
Config.init_app(app)

# Initialize processors
processor = RobustImageProcessor()
utils = ImageUtils()

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

def clear_user_files(session_id):
    """Clean up all files associated with a session"""
    try:
        # Find and delete all files with session_id
        folders = [
            Config.RAW_UPLOAD_PATH,
            Config.MASK_UPLOAD_PATH,
            Config.PROCESSED_PATH
        ]
        
        for folder in folders:
            if folder.exists():
                for file in folder.iterdir():
                    if session_id in file.name:
                        try:
                            file.unlink()
                            print(f"Deleted: {file}")
                        except Exception as e:
                            print(f"Error deleting {file}: {e}")
    except Exception as e:
        print(f"Error cleaning files: {e}")



@app.route('/')
def index():
    """Home page - Upload image"""
    # Clear previous session data
    if 'session_id' in session:
        clear_user_files(session['session_id'])
    session.clear()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Handle image upload and redirect to editor"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        original_filename = secure_filename(file.filename)
        unique_filename = f"{session_id}_{original_filename}"
        
        # Save uploaded file
        original_path = Config.RAW_UPLOAD_PATH / unique_filename
        file.save(original_path)
        
        # Store session data
        session['session_id'] = session_id
        session['original_filename'] = original_filename
        session['unique_filename'] = unique_filename
        session['upload_time'] = datetime.now().isoformat()
        session['page'] = 'editor'  # Track current page
        
        return jsonify({
            'success': True,
            'redirect': url_for('editor'),
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/editor')
def editor():
    """Editor page - Mark damage areas and adjust settings"""
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    # Get image path for display - FIXED: Now uses correct endpoint
    image_url = url_for('get_original_image', filename=session['unique_filename'])
    
    return render_template('editor.html', 
                         image_url=image_url,
                         filename=session['original_filename'],
                         session_id=session['session_id'])

@app.route('/uploads/raw/<filename>')
def get_original_image(filename):
    """Serve original uploaded images"""
    return send_from_directory(str(Config.RAW_UPLOAD_PATH), filename)

@app.route('/uploads/processed/<filename>')
def get_processed_image(filename):
    """Serve processed images"""
    return send_from_directory(str(Config.PROCESSED_PATH), filename)

@app.route('/uploads/masks/<filename>')
def get_mask_image(filename):
    """Serve mask images"""
    return send_from_directory(str(Config.MASK_UPLOAD_PATH), filename)

@app.route('/process', methods=['POST'])
def process_image():
    """Process image with mask and settings"""
    print("\n" + "="*60)
    print("RECEIVED PROCESS REQUEST")
    print("="*60)
    
    try:
        if 'session_id' not in session:
            return jsonify({'success': False, 'error': 'No active session'}), 400
        
        session_id = session['session_id']
        unique_filename = session['unique_filename']
        
        # Get parameters
        parameters = {}
        if 'parameters' in request.form and request.form['parameters']:
            parameters = json.loads(request.form['parameters'])
        
        mask_data = None
        mask_path = None
        
        # Parse mask data if provided
        if 'mask_data' in request.form and request.form['mask_data']:
            try:
                mask_json = request.form['mask_data']
                mask_data = json.loads(mask_json)
                
                print(f"Mask data received:")
                print(f"  Points: {len(mask_data.get('coordinates', []))}")
                print(f"  Brush size: {mask_data.get('brush_size', 20)}")
                
                # Create mask file
                mask_filename = f"mask_{session_id}.png"
                mask_path = Config.MASK_UPLOAD_PATH / mask_filename
                
                # Call mask creation function (you need to implement this in scratch_removal.py)
                from backend.scratch_removal import AdvancedInpainter
                inpainter = AdvancedInpainter()
                
                # Load original image to get dimensions
                original_path = Config.RAW_UPLOAD_PATH / unique_filename
                
                # Create mask from coordinates
                # Note: You need to implement create_mask_from_coordinates method in AdvancedInpainter
                mask_created = False
                try:
                    # Try to use the create_mask_from_coordinates method if it exists
                    mask_created = inpainter.create_mask_from_coordinates(
                        original_path=str(original_path),
                        coordinates=mask_data.get('coordinates', []),
                        brush_size=mask_data.get('brush_size', 20),
                        output_path=str(mask_path)
                    )
                except AttributeError:
                    # Fallback to existing method
                    import cv2
                    from PIL import Image
                    
                    # Read original image to get dimensions
                    img = cv2.imread(str(original_path))
                    if img is not None:
                        height, width = img.shape[:2]
                        
                        # Create blank mask
                        mask = np.zeros((height, width), dtype=np.uint8)
                        
                        # Draw circles at coordinates
                        for coord in mask_data.get('coordinates', []):
                            x = int(coord['x'] * (width / mask_data.get('display_width', width)))
                            y = int(coord['y'] * (height / mask_data.get('display_height', height)))
                            brush_size = int(mask_data.get('brush_size', 20) * (width / mask_data.get('display_width', width)))
                            cv2.circle(mask, (x, y), brush_size // 2, 255, -1)
                        
                        # Save mask
                        Image.fromarray(mask).save(str(mask_path))
                        mask_created = True
                
                if not mask_created:
                    mask_path = None
                    
            except Exception as e:
                print(f"Error creating mask: {e}")
                traceback.print_exc()
                mask_path = None
        
        # Process image
        original_path = Config.RAW_UPLOAD_PATH / unique_filename
        result = processor.process(str(original_path), mask_data)
        
        if not result['success']:
            return jsonify(result), 500
        
        # Save processed image
        result_filename = f"result_{session_id}.jpg"
        result_path = Config.PROCESSED_PATH / result_filename
        utils.save_image(result['processed_image'], str(result_path), quality=95)
        
        # Store result info in session
        session['result_filename'] = result_filename
        session['metrics'] = convert_numpy_types(result['metrics'])
        session['page'] = 'results'  # Update current page
        
        # Convert to base64 for response
        original_base64 = utils.numpy_to_base64(result['original_image'])
        processed_base64 = utils.numpy_to_base64(result['processed_image'])
        
        response_data = {
            'success': True,
            'original_image': original_base64,
            'processed_image': processed_base64,
            'metrics': session['metrics'],
            'filename': result_filename,
            'redirect': url_for('results'),
            'mask_used': bool(mask_path and mask_path.exists())
        }
        
        print(f"Processing successful! Redirecting to results page.")
        print("="*60 + "\n")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/results')
def results():
    """Results page - Display processed image"""
    if 'session_id' not in session or 'result_filename' not in session:
        return redirect(url_for('index'))
    
    # Get image URLs - FIXED: Using correct endpoints
    original_url = url_for('get_original_image', filename=session['unique_filename'])
    result_url = url_for('get_processed_image', filename=session['result_filename'])
    
    return render_template('results.html',
                         original_url=original_url,
                         result_url=result_url,
                         metrics=session.get('metrics', {}),
                         filename=session['original_filename'],
                         session_id=session['session_id'])

@app.route('/download/<filename>')
def download_image(filename):
    """Download processed image"""
    try:
        if 'session_id' not in session or 'result_filename' not in session:
            return redirect(url_for('index'))
        
        if session['result_filename'] != filename:
            return "Access denied", 403
        
        file_path = Config.PROCESSED_PATH / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"restored_{session['original_filename']}"
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/back')
def back():
    """Navigate back to previous page"""
    if 'page' in session:
        if session['page'] == 'results':
            # Go back to editor
            return redirect(url_for('editor'))
        elif session['page'] == 'editor':
            # Go back to upload
            if 'session_id' in session:
                clear_user_files(session['session_id'])
            session.clear()
            return redirect(url_for('index'))
    
    # Default fallback
    return redirect(url_for('index'))

@app.route('/reset')
def reset():
    """Reset everything and go to home"""
    if 'session_id' in session:
        clear_user_files(session['session_id'])
    session.clear()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    """About page with application information"""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)