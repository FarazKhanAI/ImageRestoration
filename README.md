# 🖼️ Image Restoration Studio

<div align="center">

[![Flask](https://img.shields.io/badge/Flask-3.0.0-black?logo=flask)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-blue?logo=opencv)](https://opencv.org/)
[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/🚀-Live%20Demo-orange)](https://huggingface.co/spaces/Zoro828/imageRestoration)

**Restore damaged photos with precision - Remove scratches, stains, and imperfections**

*A project by UEAS Swat Computer Systems Engineering students*

</div>

## 🌟 Live Demo

**Try it now for free:** [https://huggingface.co/spaces/Zoro828/imageRestoration](https://huggingface.co/spaces/Zoro828/imageRestoration)



## 📖 About The Project

**Image Restoration Studio** is a web application that helps you restore old or damaged photos. Using image processing algorithms, it can remove scratches, stains, watermarks, and other imperfections while preserving the original details and colors.

This project was developed as part of our studies at the **University of Engineering and Applied Sciences Swat (UEAS Swat)** in the **Department of Computer Systems Engineering (DCSE)**.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🖌️ Smart Brush Tool** | Interactive canvas for marking damage areas with adjustable brush size |
| **⚡ Fast Processing** | Restores images in 2-10 seconds using optimized algorithms |
| **🎯 Multiple Algorithms** | Choose between Telea (fast), Navier-Stokes (quality), or Hybrid methods |
| **🌈 Color Preservation** | Maintains original color consistency during restoration |
| **📱 Responsive Design** | Works perfectly on desktop, tablet, and mobile devices |
| **🎨 Built-in Editor** | Adjust brightness, contrast, saturation after processing |
| **🌓 Dark/Light Mode** | Choose your preferred theme for comfortable editing |

## 🚀 Quick Start

### Option 1: Use Online 
1. Visit **[https://huggingface.co/spaces/Zoro828/imageRestoration](https://huggingface.co/spaces/Zoro828/imageRestoration)**
2. Upload your damaged image
3. Mark the scratches or imperfections
4. Click "Process & Restore Image"
5. Download your restored photo

### Option 2: Run Locally
```bash
# Clone the repository
git clone https://github.com/FarazKhanAI/ImageRestoration.git
cd ImageRestoration

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open http://localhost:5000 in your browser
```

### Option 3: Run with Docker
```bash
# Build Docker image
docker build -t image-restoration .

# Run container
docker run -p 5000:5000 image-restoration
```

## 📸 How to Use

### Step 1: Upload Your Image
- Click "Upload Your Image" or drag & drop
- Supported formats: JPG, PNG, BMP, TIFF
- Maximum file size: 16MB

### Step 2: Mark Damage Areas
- Marking damage areas
- Use the brush tool to mark scratches or imperfections
- Adjust brush size using the slider (5-100px)
- Undo mistakes with Ctrl+Z or the Undo button
- Clear all marks if needed

### Step 3: Choose Restoration Settings
| Setting | Description | Recommended |
|---------|-------------|-------------|
| **Inpainting Method** | Algorithm for restoration | Hybrid (Best results) |
| **Brush Size** | Size of the marking brush | 20-40px (adjust as needed) |
| **Inpainting Radius** | How far to search for replacement pixels | 3-5px |

### Step 4: Process & Download
- Click "Process & Restore Image" (takes 2-10 seconds)
- View side-by-side comparison of original and restored
- Use image editor to adjust final result (optional)
- Download your restored image in high quality

## 📁 Project Structure

```
image-restoration-app/
├── 📄 app.py                    # Main Flask application
├── 📄 config.py                # Configuration settings
├── 📄 Dockerfile               # Docker configuration
├── 📄 requirements.txt         # Python dependencies
├── 📄 .env                     # Environment variables
│
├── 📁 backend/                 # Core image processing
│   ├── 📄 image_processor.py   # Main processing pipeline
│   ├── 📄 scratch_removal.py   # Inpainting algorithms
│   ├── 📄 utils.py            # Helper functions
│   ├── 📄 enhancement.py      # Color adjustments
│   └── 📄 validators.py       # Input validation
│
├── 📁 templates/              # HTML templates
│   ├── 📄 base.html          # Base layout with navigation
│   ├── 📄 index.html         # Upload page
│   ├── 📄 editor.html        # Image editor with canvas
│   ├── 📄 results.html       # Results comparison
│   └── 📄 about.html         # Project information
│
├── 📁 static/                # Web assets
│   ├── 📁 css/              # Stylesheets
│   ├── 📁 js/               # JavaScript files
│   └── 📁 images/           # Icons and logos
│
└── 📁 instance/             # User data (created automatically)
    ├── 📁 uploads/raw/      # Original uploaded images
    ├── 📁 uploads/masks/    # Generated mask images
    └── 📁 processed/        # Restored output images
```

## 🔧 Technical Details

### Tech Stack
- **Backend**: Flask 3.0, OpenCV 4.8, NumPy 1.24, Pillow 10.1
- **Frontend**: HTML5, CSS3, Vanilla JavaScript, Canvas API
- **Deployment**: Docker, Hugging Face Spaces, Gunicorn
- **Algorithms**: Telea Inpainting, Navier-Stokes Inpainting, Hybrid Approach

### Image Processing Pipeline
```
1. Upload → Validate → Resize if needed
2. Convert coordinates to mask → Apply feathering
3. Select algorithm → Apply inpainting
4. Color correction → Post-processing
5. Save result → Generate comparison
6. Cleanup temporary files
```

### Performance Metrics
| Image Size | Processing Time | Memory Usage |
|------------|----------------|--------------|
| 800×600 | 1-3 seconds | ~50MB |
| 1920×1080 | 3-7 seconds | ~100MB |
| 4000×3000 | 7-15 seconds | ~200MB |

## 🎓 Team

### Project Members
- **Faraz Khan** 
- **Gul-e-Rana**   
- **Jawad Khan** 

### Institution
**University of Engineering and Applied Sciences Swat (UEAS Swat)**  
**Department of Computer Systems Engineering (DCSE)**  

*This project was developed as part of our coursework in Digital Image Processing.*

## 🌍 Deployment

### Deployed on Hugging Face
Our application is live on Hugging Face Spaces:
- **URL**: [https://huggingface.co/spaces/Zoro828/imageRestoration](https://huggingface.co/spaces/Zoro828/imageRestoration)
- **SDK**: Docker
- **Hardware**: CPU Basic
- **Auto-deploy**: Enabled on Git push

### Self-hosting Instructions
```bash
# 1. Clone repository
git clone https://github.com/FarazKhanAI/ImageRestoration.git

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env with your settings

# 5. Run the application
python app.py
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
export FLASK_ENV=development
python app.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

We would like to thank:
- **UEAS Swat Faculty** for guidance and support
- **OpenCV Community** for the powerful computer vision library
- **Flask Team** for the lightweight web framework
- **Hugging Face** for providing free hosting on Spaces

## 🔗 Useful Links

- **Live Demo**: [https://huggingface.co/spaces/Zoro828/imageRestoration](https://huggingface.co/spaces/Zoro828/imageRestoration)
- **Source Code**: [https://github.com/FarazKhanAI/ImageRestoration](https://github.com/FarazKhanAI/ImageRestoration)
- **Issue Tracker**: [https://github.com/FarazKhanAI/ImageRestoration/issues](https://github.com/FarazKhanAI/ImageRestoration/issues)

---

<div align="center">

### ✨ **Ready to restore your memories?**
**[Try it now →](https://huggingface.co/spaces/Zoro828/imageRestoration)**

*Made with ❤️ by UEAS Swat DCSE students*

</div>