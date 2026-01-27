# 🖼️ Image Restoration Studio

<div align="center">

[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-5C3EE8?style=for-the-badge&logo=opencv)](https://opencv.org/)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Restore old photos, remove scratches, and enhance image quality with AI-powered inpainting**

[Live Demo](#) • [Report Bug](https://github.com/FarazKhanAI/ImageRestoration/issues) • [Request Feature](https://github.com/FarazKhanAI/ImageRestoration/issues)

</div>

## ✨ Features

### 🎨 **Interactive Restoration**
- **Draw Directly**: Mark scratches and damage with brush tool
- **Real-time Preview**: See adjustments instantly
- **Multi-Algorithm**: Telea (fast) and Navier-Stokes (quality) inpainting

### 🔧 **Smart Enhancements**
- Brightness/Contrast/Saturation controls
- Noise reduction & detail enhancement
- Auto white balance & gamma correction
- Quality metrics (PSNR, SSIM, processing time)

### 📱 **Modern Interface**
- Clean, responsive design
- Before/After comparison
- One-click download
- Mobile-friendly

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Conda (recommended)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/FarazKhanAI/ImageRestoration.git
cd ImageRestoration

# 2. Create environment
conda create -n image-restoration python=3.10
conda activate image-restoration

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open **http://localhost:5000** in your browser.

## 📖 How to Use

### 1. **Upload Image**
   - Drag & drop or click to browse
   - Supports JPG, PNG, BMP, TIFF (max 16MB)

### 2. **Mark Damage**
   - Use brush tool to mark scratches
   - Adjust brush size (5-100px)
   - Undo/clear as needed

### 3. **Adjust Settings**
   - **Basic**: Brightness, Contrast, Saturation
   - **Enhance**: Sharpness, Noise Reduction
   - **Restore**: Inpainting method, Gamma correction

### 4. **Process & Download**
   - Click "Process & Restore"
   - View quality metrics
   - Download restored image

## 🏗️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Flask 3.0 + OpenCV 4.8 | Image processing & web server |
| **Processing** | NumPy, Scikit-image | Computer vision algorithms |
| **Performance** | Numba, Joblib | Speed optimization |
| **Frontend** | HTML5 Canvas + JavaScript | Interactive UI |
| **Deployment** | Gunicorn | Production-ready server |

## 📁 Project Structure

```
ImageRestoration/
├── app.py                    # Main Flask application
├── config.py                # Configuration settings
├── requirements.txt         # Dependencies
├── README.md               # This file
│
├── backend/                # Core processing logic
│   ├── image_processor.py  # Main pipeline
│   ├── enhancement.py      # Image adjustments
│   ├── scratch_removal.py  # Damage repair
│   ├── utils.py           # Helper functions
│   └── validators.py      # Input validation
│
├── static/                 # Frontend assets
│   ├── css/style.css      # Styling
│   └── js/main.js         # Interactive features
│
├── templates/              # HTML pages
│   ├── base.html          # Layout template
│   └── index.html         # Main interface
│
└── instance/              # User data (ignored in git)
    ├── uploads/           # Original images
    └── processed/         # Restored results
```

## 🔬 Algorithms Used

| Algorithm | Purpose | Speed |
|-----------|---------|-------|
| **Fast Non-local Means** | Noise reduction | ⚡ Fast |
| **CLAHE** | Detail enhancement | ⚡ Fast |
| **Telea Inpainting** | Scratch removal | ⚡ Fast |
| **Navier-Stokes** | Quality inpainting | 🐢 Accurate |
| **Neighbor Interpolation** | Pixel restoration | ⚡ Fast |

## 🚢 Deployment

### Local Development
```bash
python app.py
```

### Production (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)
```dockerfile
FROM python:3.10-slim
COPY . /app
RUN pip install -r requirements.txt
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📊 Performance

| Image Size | Processing Time | Memory Usage |
|------------|----------------|--------------|
| 1MP (1024×768) | < 2 seconds | ~100MB |
| 5MP (2592×1944) | < 10 seconds | ~300MB |
| 12MP (4000×3000) | < 30 seconds | ~500MB |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📧 Contact

Faraz Khan - [GitHub Issues](https://github.com/FarazKhanAI/ImageRestoration/issues)

Project Link: [https://github.com/FarazKhanAI/ImageRestoration](https://github.com/FarazKhanAI/ImageRestoration)

## 🙏 Acknowledgments

- [OpenCV](https://opencv.org/) - Computer vision library
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Scikit-image](https://scikit-image.org/) - Image processing algorithms

---

<div align="center">
  <p><strong>✨ Bring old memories back to life ✨</strong></p>
  <sub>Built with ❤️ using Flask & OpenCV</sub>
</div>