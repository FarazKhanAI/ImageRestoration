from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, send_from_directory
import os
import json
import uuid
from pathlib import Path
import numpy as np
import traceback
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config

# Add current directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import backend modules
try:
    from backend.image_processor import RobustImageProcessor
    from backend.utils import ImageUtils
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in backend/: {os.listdir('backend') if os.path.exists('backend') else 'No backend folder'}")
    raise

# Initialize Flask app WITHOUT session
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'imagerestoration924502@flaskapp')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure directories exist
Config.init_app(app)

# Initialize processors
processor = RobustImageProcessor()
utils = ImageUtils()

# Store active sessions in memory (will reset on restart)
active_sessions = {}

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
                        except Exception as e:
                            print(f"Error deleting {file}: {e}")
    except Exception as e:
        print(f"Error cleaning files: {e}")

@app.route('/')
def index():
    """Home page - Upload image"""
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
        
        # Store session data in memory
        active_sessions[session_id] = {
            'session_id': session_id,
            'original_filename': original_filename,
            'unique_filename': unique_filename,
            'upload_time': datetime.now().isoformat()
        }
        
        # Return session_id in the redirect URL
        return jsonify({
            'success': True,
            'redirect': f'/editor?session_id={session_id}',
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/editor')
def editor():
    """Editor page - Mark damage areas and adjust settings"""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in active_sessions:
        return redirect(url_for('index'))
    
    session_data = active_sessions[session_id]
    
    # Get image path for display
    image_url = url_for('get_original_image', filename=session_data['unique_filename'])
    
    return render_template('editor.html', 
                         image_url=image_url,
                         filename=session_data['original_filename'],
                         session_id=session_id)

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
    try:
        session_id = request.form.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({'success': False, 'error': 'No active session'}), 400
        
        session_data = active_sessions[session_id]
        unique_filename = session_data['unique_filename']
        
        # Get parameters
        parameters = {}
        if 'parameters' in request.form and request.form['parameters']:
            parameters = json.loads(request.form['parameters'])
        
        mask_data = None
        
        # Parse mask data if provided
        if 'mask_data' in request.form and request.form['mask_data']:
            try:
                mask_json = request.form['mask_data']
                mask_data = json.loads(mask_json)
            except Exception as e:
                print(f"Error parsing mask data: {e}")
        
        # Process image
        original_path = Config.RAW_UPLOAD_PATH / unique_filename
        result = processor.process(str(original_path), mask_data)
        
        if not result['success']:
            return jsonify(result), 500
        
        # Save processed image
        result_filename = f"result_{session_id}.jpg"
        result_path = Config.PROCESSED_PATH / result_filename
        utils.save_image(result['processed_image'], str(result_path), quality=95)
        
        # Update session data
        session_data['result_filename'] = result_filename
        session_data['metrics'] = result['metrics']
        active_sessions[session_id] = session_data
        
        # Convert to base64 for response
        original_base64 = utils.numpy_to_base64(result['original_image'])
        processed_base64 = utils.numpy_to_base64(result['processed_image'])
        
        response_data = {
            'success': True,
            'original_image': original_base64,
            'processed_image': processed_base64,
            'metrics': session_data['metrics'],
            'filename': result_filename,
            'redirect': f'/results?session_id={session_id}',
            'mask_used': bool(mask_data)
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Processing error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/results')
def results():
    """Results page - Display processed image"""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in active_sessions:
        return redirect(url_for('index'))
    
    session_data = active_sessions[session_id]
    
    if 'result_filename' not in session_data:
        return redirect(url_for('index'))
    
    # Get image URLs
    original_url = url_for('get_original_image', filename=session_data['unique_filename'])
    result_url = url_for('get_processed_image', filename=session_data['result_filename'])
    
    return render_template('results.html',
                         original_url=original_url,
                         result_url=result_url,
                         metrics=session_data.get('metrics', {}),
                         filename=session_data['original_filename'],
                         session_id=session_id)

@app.route('/download/<filename>')
def download_image(filename):
    """Download processed image"""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return "Access denied", 403
        
        session_data = active_sessions[session_id]
        
        if session_data.get('result_filename') != filename:
            return "Access denied", 403
        
        file_path = Config.PROCESSED_PATH / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"restored_{session_data['original_filename']}"
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/back')
def back():
    """Navigate back to previous page"""
    session_id = request.args.get('session_id')
    referrer = request.referrer
    
    if session_id:
        if '/results' in str(referrer):
            return redirect(f'/editor?session_id={session_id}')
        elif '/editor' in str(referrer):
            # Clean up files and remove session
            if session_id in active_sessions:
                clear_user_files(session_id)
                active_sessions.pop(session_id, None)
    
    return redirect(url_for('index'))

@app.route('/reset')
def reset():
    """Reset everything and go to home"""
    session_id = request.args.get('session_id')
    
    if session_id and session_id in active_sessions:
        clear_user_files(session_id)
        active_sessions.pop(session_id, None)
    
    return redirect(url_for('index'))

@app.route('/about')
def about():
    """About page with application information"""
    return render_template('about.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)