# 🖼️ Image Restoration Studio

<div align="center">

[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-5C3EE8?style=for-the-badge&logo=opencv)](https://opencv.org/)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-2ecc71?style=for-the-badge)]()

**Professional-grade image restoration with multi-algorithm inpainting**

[Live Demo](#) • [Report Bug](https://github.com/FarazKhanAI/ImageRestoration/issues) • [Request Feature](https://github.com/FarazKhanAI/ImageRestoration/issues)

<img src="https://github.com/FarazKhanAI/ImageRestoration/blob/main/demo.gif?raw=true" width="600" alt="Image Restoration Demo">

</div>

## 🎯 What It Does

Restore damaged photos with AI-powered precision. Remove scratches, blemishes, and unwanted objects while preserving original details and colors.

### ✨ **Key Features**
- ✅ **Multi-Algorithm Inpainting** - Combines Telea, Navier-Stokes, and hybrid methods
- ✅ **Smart Mask Processing** - Feathering and edge-aware mask creation
- ✅ **Color Preservation** - Maintains original color consistency
- ✅ **Fast Processing** - 2-10 seconds for most images
- ✅ **Batch Processing** - Automatically saves masks and results

## 🚀 **Get Started in 2 Minutes**

### **Prerequisites**
- Python 3.10 or higher
- Git (optional)

### **Installation**

```bash
# 1. Clone the repository
git clone https://github.com/FarazKhanAI/ImageRestoration.git
cd ImageRestoration

# 2. Create virtual environment (optional but recommended)
python -m venv venv

# 3. Activate environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
python app.py
```

**Open your browser and visit:** `http://localhost:5000`

## 📖 **How to Use**

### **Step 1: Upload Image**
- Drag & drop your image or click to browse
- Supports JPG, PNG, BMP, TIFF (up to 16MB)

### **Step 2: Mark Damage Areas**
- Use the brush tool to mark scratches, stains, or objects
- Adjust brush size with the slider
- Use Undo/Clear if needed

### **Step 3: Adjust Parameters**
- **Inpainting Method**: 
  - `Fast (Telea)` - Quick restoration
  - `Quality (Navier-Stokes)` - Better for textures
  - `Hybrid` - Best overall (recommended)
- **Brush Size**: 5-100px
- **Inpainting Radius**: 1-20px

### **Step 4: Process & Download**
- Click "Process & Restore Image"
- View before/after comparison
- Download restored image in high quality

## 🏗️ **Technical Architecture**

### **Backend Stack**
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | Flask 3.0 | REST API & routing |
| **Image Processing** | OpenCV 4.8 | Core inpainting algorithms |
| **Performance** | Numba | JIT compilation for speed |
| **Math Operations** | NumPy | Matrix operations |
| **Image I/O** | Pillow | Image format handling |

### **Processing Pipeline**
```
1. Image Upload → Validation → Resize
2. Mask Creation → Feathering → Dilation
3. Inpainting Selection → Algorithm execution
4. Color Correction → Post-processing
5. Result Generation → Metrics calculation
```

## 📁 **Project Structure**

```
image-restoration-app/
├── app.py                    # Main Flask application
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
│
├── backend/                 # Core processing logic
│   ├── image_processor.py   # Main processing pipeline
│   ├── scratch_removal.py   # Advanced inpainting algorithms
│   ├── utils.py            # Helper functions (mask creation, I/O)
│   ├── enhancement.py      # Color adjustments (optional)
│   └── validators.py       # Input validation
│
├── templates/               # Frontend HTML
│   ├── base.html           # Base layout
│   └── index.html          # Main interface
│
├── static/                  # Web assets
│   ├── css/style.css       # Styling
│   └── js/main.js          # Interactive features
│
└── instance/               # User data (not in git)
    ├── uploads/raw/        # Original uploaded images
    ├── uploads/masks/      # Generated mask images
    └── processed/          # Restored output images
```

## 🧠 **Advanced Inpainting Algorithms**

### **Multi-Algorithm Strategy**
The system intelligently selects the best algorithm based on damage size:

| Damage Size | Algorithm Used | Processing Time | Best For |
|-------------|----------------|-----------------|----------|
| **Small** (<1%) | Fast Telea | <2 seconds | Scratches, spots |
| **Medium** (1-10%) | Navier-Stokes | 2-5 seconds | Textured areas |
| **Large** (>10%) | Hybrid Approach | 5-15 seconds | Large object removal |

### **Key Technical Improvements**
1. **Edge Preservation** - Uses Canny edge detection to protect boundaries
2. **Color Matching** - Adjusts inpainted colors to match surroundings
3. **Multi-Scale Processing** - Handles different damage sizes optimally
4. **Soft Mask Blending** - Feathering prevents visible seams

## ⚡ **Performance & Optimization**

### **Processing Times**
| Image Resolution | Mask Size | Processing Time |
|------------------|-----------|-----------------|
| 800×600 | Small | 1-3 seconds |
| 1920×1080 | Medium | 3-7 seconds |
| 4000×3000 | Large | 7-15 seconds |

### **Memory Usage**
- **Minimal footprint**: ~100MB for typical images
- **Auto-resizing**: Large images automatically scaled to 2000px max dimension
- **Efficient cleanup**: Temporary files removed after processing

## 🚢 **Deployment Options**

### **Option 1: Local Development**
```bash
python app.py
# Runs on http://localhost:5000 with debug mode
```

### **Option 2: Production with Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### **Option 3: Free Cloud Deployment**
#### **Render.com** (Recommended)
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python app.py`
4. Get free HTTPS and auto-deploy

#### **PythonAnywhere**
1. Upload files via web interface
2. Configure WSGI file
3. Free tier available (limited)

## 🔧 **Configuration**

### **Environment Variables**
Create `.env` file for production:
```env
SECRET_KEY=your-secret-key-here
MAX_CONTENT_LENGTH=16777216  # 16MB
DEBUG=False
```

### **Directory Setup**
The application automatically creates:
```
instance/              # Created automatically
├── uploads/raw/      # Original images
├── uploads/masks/    # Mask images (saved here!)
└── processed/        # Final results
```

## 🐛 **Troubleshooting**

### **Common Issues & Solutions**

| Issue | Solution |
|-------|----------|
| **Mask not appearing** | Check browser console for errors, ensure you're drawing on the canvas |
| **Processing too slow** | Reduce image size before uploading (max 2000px recommended) |
| **Color mismatch** | Try the "Hybrid" inpainting method for better color preservation |
| **Blank results** | Check server logs for errors, verify image format is supported |

### **Debug Mode**
Enable debug logging by setting `DEBUG = True` in `app.py`:
```python
# In app.py
DEBUG = True
```

## 🤝 **Contributing**

We welcome contributions! Here's how to help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/improvement`)
3. **Commit** your changes (`git commit -m 'Add some improvement'`)
4. **Push** to the branch (`git push origin feature/improvement`)
5. **Open** a Pull Request

### **Development Setup**
```bash
# Clone and setup
git clone https://github.com/FarazKhanAI/ImageRestoration.git
cd ImageRestoration
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Format code
black .
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 **Support & Contact**

- **GitHub Issues**: [Report bugs or request features](https://github.com/FarazKhanAI/ImageRestoration/issues)
- **Email**: [Your email or project email]
- **Project Link**: [https://github.com/FarazKhanAI/ImageRestoration](https://github.com/FarazKhanAI/ImageRestoration)

## 🙏 **Acknowledgments**

Special thanks to:
- **OpenCV Team** - For the incredible computer vision library
- **Flask Community** - For the lightweight web framework
- **All Contributors** - Who help improve this project

---

<div align="center">

### **Ready to restore your images?**
[Get Started Now](#-get-started-in-2-minutes) | [View Demo](#)

Made with ❤️ using Flask & OpenCV

</div>

## 📚 **Next Steps**

### **Planned Improvements**
- [ ] **Batch Processing** - Restore multiple images at once
- [ ] **AI Enhancement** - Add deep learning models for better results
- [ ] **Mobile App** - iOS/Android companion apps
- [ ] **Cloud Storage** - Google Drive/Dropbox integration

### **Frontend Updates** (Coming Soon)
- Dark mode toggle
- More brush styles and shapes
- Real-time preview while drawing
- Advanced comparison slider

---

**Tip**: For best results, use high-quality source images and mark damage areas precisely with appropriate brush size.