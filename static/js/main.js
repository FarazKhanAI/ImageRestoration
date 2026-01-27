class ImageRestorationApp {
    constructor() {
        this.originalImage = null;
        this.currentImage = null;
        this.maskCanvas = null;
        this.maskCtx = null;
        this.imageCanvas = null;
        this.imageCtx = null;
        this.isDrawing = false;
        this.brushSize = 20;
        this.brushColor = 'rgba(255, 0, 0, 0.7)';
        this.lastX = 0;
        this.lastY = 0;
        this.maskData = [];
        this.processingParams = {
            brightness: 0,
            contrast: 0,
            sharpness: 0,
            saturation: 100,
            noise_reduction: 0,
            detail_enhancement: 0,
            auto_white_balance: false,
            gamma: 1.0,
            inpainting_method: 'telea',
            inpainting_radius: 3,
            brush_size: 20
        };
        
        this.initializeElements();
        this.bindEvents();
        this.loadFromLocalStorage();
    }
    
    initializeElements() {
        // Get DOM elements
        this.elements = {
            uploadArea: document.getElementById('uploadArea'),
            fileInput: document.getElementById('fileInput'),
            imageCanvas: document.getElementById('imageCanvas'),
            maskCanvas: document.getElementById('maskCanvas'),
            brushSizeInput: document.getElementById('brushSize'),
            brushSizeValue: document.getElementById('brushSizeValue'),
            clearMaskBtn: document.getElementById('clearMask'),
            undoBtn: document.getElementById('undo'),
            editorSection: document.getElementById('editorSection'),
            uploadSection: document.getElementById('uploadSection'),
            processingSection: document.getElementById('processingSection'),
            resultsSection: document.getElementById('resultsSection'),
            processBtn: document.getElementById('processBtn'),
            newImageBtn: document.getElementById('newImageBtn'),
            downloadBtn: document.getElementById('downloadBtn'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            originalImage: document.getElementById('originalImage'),
            processedImage: document.getElementById('processedImage'),
            processingTime: document.getElementById('processingTime'),
            psnrValue: document.getElementById('psnrValue'),
            ssimValue: document.getElementById('ssimValue'),
            improvementValue: document.getElementById('improvementValue')
        };
        
        // Get all slider inputs
        this.sliders = {
            brightness: document.getElementById('brightness'),
            contrast: document.getElementById('contrast'),
            sharpness: document.getElementById('sharpness'),
            saturation: document.getElementById('saturation'),
            noiseReduction: document.getElementById('noiseReduction'),
            detailEnhancement: document.getElementById('detailEnhancement'),
            gamma: document.getElementById('gamma'),
            inpaintingRadius: document.getElementById('inpaintingRadius')
        };
        
        // Get all value displays
        this.valueDisplays = {
            brightness: document.getElementById('brightnessValue'),
            contrast: document.getElementById('contrastValue'),
            sharpness: document.getElementById('sharpnessValue'),
            saturation: document.getElementById('saturationValue'),
            noiseReduction: document.getElementById('noiseReductionValue'),
            detailEnhancement: document.getElementById('detailEnhancementValue'),
            gamma: document.getElementById('gammaValue'),
            inpaintingRadius: document.getElementById('inpaintingRadiusValue')
        };
        
        // Initialize canvas contexts
        this.imageCtx = this.elements.imageCanvas.getContext('2d');
        this.maskCtx = this.elements.maskCanvas.getContext('2d');
        
        // Set initial brush size display
        this.updateBrushSizeDisplay();
    }
    
    bindEvents() {
        // File upload events
        this.elements.uploadArea.addEventListener('click', () => {
            this.elements.fileInput.click();
        });
        
        this.elements.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.elements.uploadArea.classList.add('drag-over');
        });
        
        this.elements.uploadArea.addEventListener('dragleave', () => {
            this.elements.uploadArea.classList.remove('drag-over');
        });
        
        this.elements.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.elements.uploadArea.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length > 0) {
                this.handleFileSelect(e.dataTransfer.files[0]);
            }
        });
        
        this.elements.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });
        
        // Canvas drawing events
        this.elements.imageCanvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.elements.imageCanvas.addEventListener('mousemove', (e) => this.draw(e));
        this.elements.imageCanvas.addEventListener('mouseup', () => this.stopDrawing());
        this.elements.imageCanvas.addEventListener('mouseleave', () => this.stopDrawing());
        
        // Touch events for mobile
        this.elements.imageCanvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startDrawing(e.touches[0]);
        });
        
        this.elements.imageCanvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            this.draw(e.touches[0]);
        });
        
        this.elements.imageCanvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopDrawing();
        });
        
        // Brush size control
        this.elements.brushSizeInput.addEventListener('input', (e) => {
            this.brushSize = parseInt(e.target.value);
            this.updateBrushSizeDisplay();
        });
        
        // Mask controls
        this.elements.clearMaskBtn.addEventListener('click', () => this.clearMask());
        this.elements.undoBtn.addEventListener('click', () => this.undoLastStroke());
        
        // Processing button
        this.elements.processBtn.addEventListener('click', () => this.processImage());
        this.elements.newImageBtn.addEventListener('click', () => this.resetApp());
        this.elements.downloadBtn.addEventListener('click', () => this.downloadProcessedImage());
        
        // Slider events
        for (const [key, slider] of Object.entries(this.sliders)) {
            slider.addEventListener('input', (e) => {
                const value = key === 'gamma' ? parseFloat(e.target.value) : parseInt(e.target.value);
                this.processingParams[key] = value;
                this.updateValueDisplay(key, value);
                this.saveToLocalStorage();
                
                // Preview enhancement for basic adjustments
                if (['brightness', 'contrast', 'saturation'].includes(key)) {
                    this.previewEnhancement(key, value);
                }
            });
        }
        
        // Inpainting method selection
        document.querySelectorAll('input[name="inpainting_method"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.processingParams.inpainting_method = e.target.value;
                this.saveToLocalStorage();
            });
        });
        
        // Auto white balance checkbox
        document.getElementById('autoWhiteBalance').addEventListener('change', (e) => {
            this.processingParams.auto_white_balance = e.target.checked;
            this.saveToLocalStorage();
        });
        
        // Load saved parameters on page load
        window.addEventListener('load', () => {
            this.updateAllValueDisplays();
        });
    }
    
    handleFileSelect(file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff'];
        if (!validTypes.includes(file.type)) {
            alert('Please select a valid image file (JPEG, PNG, BMP, TIFF)');
            return;
        }
        
        // Validate file size (16MB max)
        if (file.size > 16 * 1024 * 1024) {
            alert('File size must be less than 16MB');
            return;
        }
        
        // Show loading
        this.showLoading();
        
        // Read and display image
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                this.originalImage = img;
                this.currentImage = img;
                this.displayImage(img);
                this.switchToEditor();
                this.hideLoading();
                
                // Save file info for upload
                this.selectedFile = file;
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    displayImage(img) {
        const canvas = this.elements.imageCanvas;
        const maskCanvas = this.elements.maskCanvas;
        
        // Calculate dimensions to fit in container (max 800px width/height)
        const maxWidth = 800;
        const maxHeight = 600;
        
        let width = img.width;
        let height = img.height;
        
        if (width > maxWidth || height > maxHeight) {
            const ratio = Math.min(maxWidth / width, maxHeight / height);
            width = Math.floor(width * ratio);
            height = Math.floor(height * ratio);
        }
        
        // Set canvas dimensions
        canvas.width = width;
        canvas.height = height;
        maskCanvas.width = width;
        maskCanvas.height = height;
        
        // Clear canvases
        this.imageCtx.clearRect(0, 0, width, height);
        this.maskCtx.clearRect(0, 0, width, height);
        
        // Draw image
        this.imageCtx.drawImage(img, 0, 0, width, height);
        
        // Store display dimensions for coordinate mapping
        this.displayWidth = width;
        this.displayHeight = height;
        this.imageAspectRatio = img.width / img.height;
        
        // Reset mask data
        this.maskData = [];
    }
    
    startDrawing(e) {
        this.isDrawing = true;
        const pos = this.getCanvasPosition(e);
        this.lastX = pos.x;
        this.lastY = pos.y;
        
        // Draw initial point
        this.drawPoint(pos.x, pos.y);
        this.maskData.push({x: pos.x, y: pos.y});
    }
    
    draw(e) {
        if (!this.isDrawing) return;
        
        const pos = this.getCanvasPosition(e);
        this.drawLine(this.lastX, this.lastY, pos.x, pos.y);
        this.maskData.push({x: pos.x, y: pos.y});
        
        this.lastX = pos.x;
        this.lastY = pos.y;
    }
    
    stopDrawing() {
        this.isDrawing = false;
        this.saveToLocalStorage();
    }
    
    drawPoint(x, y) {
        this.maskCtx.beginPath();
        this.maskCtx.arc(x, y, this.brushSize / 2, 0, Math.PI * 2);
        this.maskCtx.fillStyle = this.brushColor;
        this.maskCtx.fill();
    }
    
    drawLine(x1, y1, x2, y2) {
        this.maskCtx.beginPath();
        this.maskCtx.moveTo(x1, y1);
        this.maskCtx.lineTo(x2, y2);
        this.maskCtx.lineWidth = this.brushSize;
        this.maskCtx.lineCap = 'round';
        this.maskCtx.strokeStyle = this.brushColor;
        this.maskCtx.stroke();
    }
    
    getCanvasPosition(e) {
        const canvas = this.elements.imageCanvas;
        const rect = canvas.getBoundingClientRect();
        
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
    
    updateBrushSizeDisplay() {
        this.elements.brushSizeValue.textContent = this.brushSize;
        this.processingParams.brush_size = this.brushSize;
    }
    
    clearMask() {
        this.maskCtx.clearRect(0, 0, this.elements.maskCanvas.width, this.elements.maskCanvas.height);
        this.maskData = [];
        this.saveToLocalStorage();
    }
    
    undoLastStroke() {
        if (this.maskData.length === 0) return;
        
        // Simple undo: clear and redraw all except last stroke
        // In a production app, you'd want to implement a proper undo stack
        this.maskCtx.clearRect(0, 0, this.elements.maskCanvas.width, this.elements.maskCanvas.height);
        
        // Remove last stroke data (simplified)
        if (this.maskData.length > 10) { // Assume each stroke has about 10 points
            this.maskData = this.maskData.slice(0, -10);
        } else {
            this.maskData = [];
        }
        
        // Redraw remaining mask data
        this.redrawMask();
        this.saveToLocalStorage();
    }
    
    redrawMask() {
        if (this.maskData.length === 0) return;
        
        this.maskCtx.beginPath();
        this.maskCtx.moveTo(this.maskData[0].x, this.maskData[0].y);
        
        for (let i = 1; i < this.maskData.length; i++) {
            this.maskCtx.lineTo(this.maskData[i].x, this.maskData[i].y);
        }
        
        this.maskCtx.lineWidth = this.brushSize;
        this.maskCtx.lineCap = 'round';
        this.maskCtx.strokeStyle = this.brushColor;
        this.maskCtx.stroke();
    }
    
    async processImage() {
        if (!this.selectedFile) {
            alert('Please upload an image first');
            return;
        }
        
        this.showLoading();
        this.elements.processingSection.style.display = 'block';
        this.elements.editorSection.style.display = 'none';
        
        try {
            // Prepare form data
            const formData = new FormData();
            formData.append('image', this.selectedFile);
            
            // Add mask data if exists
            if (this.maskData.length > 0) {
                const maskData = JSON.stringify({
                    coordinates: this.maskData,
                    brush_size: this.brushSize,
                    image_width: this.displayWidth,
                    image_height: this.displayHeight
                });
                formData.append('mask_data', maskData);
            }
            
            // Add processing parameters
            formData.append('parameters', JSON.stringify(this.processingParams));
            
            // Send to server
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayResults(result);
            } else {
                throw new Error(result.error || 'Processing failed');
            }
            
        } catch (error) {
            console.error('Processing error:', error);
            alert('Error processing image: ' + error.message);
            this.switchToEditor();
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults(result) {
        // Display original and processed images
        this.elements.originalImage.src = result.original_image;
        this.elements.processedImage.src = result.processed_image;
        
        // Display metrics
        this.elements.processingTime.textContent = result.metrics.processing_time + 's';
        this.elements.psnrValue.textContent = result.metrics.psnr;
        this.elements.ssimValue.textContent = result.metrics.ssim;
        this.elements.improvementValue.textContent = result.metrics.improvement;
        
        // Store processed image data for download
        this.processedImageData = result.processed_image;
        this.processedFilename = result.filename;
        
        // Show results section
        this.elements.processingSection.style.display = 'none';
        this.elements.resultsSection.style.display = 'block';
    }
    
    previewEnhancement(type, value) {
        if (!this.originalImage) return;
        
        // Create a temporary canvas for preview
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = this.displayWidth;
        tempCanvas.height = this.displayHeight;
        
        // Apply enhancement (simplified client-side preview)
        tempCtx.filter = this.getFilterForEnhancement(type, value);
        tempCtx.drawImage(this.originalImage, 0, 0, this.displayWidth, this.displayHeight);
        
        // Draw mask on top
        tempCtx.drawImage(this.elements.maskCanvas, 0, 0);
        
        // Update display
        this.imageCtx.clearRect(0, 0, this.displayWidth, this.displayHeight);
        this.imageCtx.drawImage(tempCanvas, 0, 0);
    }
    
    getFilterForEnhancement(type, value) {
        switch(type) {
            case 'brightness':
                return `brightness(${100 + value}%)`;
            case 'contrast':
                return `contrast(${100 + value}%)`;
            case 'saturation':
                return `saturate(${value}%)`;
            default:
                return 'none';
        }
    }
    
    switchToEditor() {
        this.elements.uploadSection.style.display = 'none';
        this.elements.editorSection.style.display = 'block';
        this.elements.resultsSection.style.display = 'none';
    }
    
    resetApp() {
        // Reset all elements
        this.elements.uploadSection.style.display = 'block';
        this.elements.editorSection.style.display = 'none';
        this.elements.resultsSection.style.display = 'none';
        
        // Clear file input
        this.elements.fileInput.value = '';
        this.selectedFile = null;
        this.originalImage = null;
        this.currentImage = null;
        
        // Clear canvases
        this.imageCtx.clearRect(0, 0, this.displayWidth, this.displayHeight);
        this.maskCtx.clearRect(0, 0, this.displayWidth, this.displayHeight);
        
        // Reset mask data
        this.maskData = [];
    }
    
    downloadProcessedImage() {
        if (!this.processedImageData) return;
        
        // Create a temporary link element
        const link = document.createElement('a');
        link.href = this.processedImageData;
        link.download = this.processedFilename || 'restored_image.jpg';
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    showLoading() {
        this.elements.loadingOverlay.style.display = 'flex';
    }
    
    hideLoading() {
        this.elements.loadingOverlay.style.display = 'none';
    }
    
    updateValueDisplay(key, value) {
        if (this.valueDisplays[key]) {
            if (key === 'gamma') {
                this.valueDisplays[key].textContent = value.toFixed(2);
            } else {
                this.valueDisplays[key].textContent = value;
            }
        }
    }
    
    updateAllValueDisplays() {
        for (const [key, value] of Object.entries(this.processingParams)) {
            this.updateValueDisplay(key, value);
        }
    }
    
    saveToLocalStorage() {
        const data = {
            processingParams: this.processingParams,
            maskData: this.maskData,
            brushSize: this.brushSize
        };
        localStorage.setItem('imageRestorationApp', JSON.stringify(data));
    }
    
    loadFromLocalStorage() {
        const saved = localStorage.getItem('imageRestorationApp');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                this.processingParams = {...this.processingParams, ...data.processingParams};
                this.maskData = data.maskData || [];
                this.brushSize = data.brushSize || 20;
                
                // Update UI elements
                this.elements.brushSizeInput.value = this.brushSize;
                this.updateBrushSizeDisplay();
                this.updateAllValueDisplays();
                
                // Set radio buttons
                document.querySelector(`input[name="inpainting_method"][value="${this.processingParams.inpainting_method}"]`).checked = true;
                document.getElementById('autoWhiteBalance').checked = this.processingParams.auto_white_balance;
                
                // Set slider values
                for (const [key, slider] of Object.entries(this.sliders)) {
                    slider.value = this.processingParams[key];
                }
                
            } catch (e) {
                console.error('Error loading saved data:', e);
            }
        }
    }
}

// Initialize app when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ImageRestorationApp();
});