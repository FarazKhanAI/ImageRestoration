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
        this.resizeTimeout = null;
        this.selectedFile = null;
        this.processedImageData = null;
        this.processedFilename = null;
        this.displayWidth = 0;
        this.displayHeight = 0;
        this.originalWidth = 0;
        this.originalHeight = 0;
        this.imageAspectRatio = 1;
        this.canvasScale = 1;
        
        // Updated processing parameters (only essentials)
        this.processingParams = {
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
        
        // Get slider inputs (only the ones that exist now)
        this.sliders = {
            gamma: document.getElementById('gamma'),
            inpaintingRadius: document.getElementById('inpaintingRadius')
        };
        
        // Get value displays
        this.valueDisplays = {
            gamma: document.getElementById('gammaValue'),
            inpaintingRadius: document.getElementById('inpaintingRadiusValue')
        };
        
        // Initialize canvas contexts
        this.imageCtx = this.elements.imageCanvas.getContext('2d');
        this.maskCtx = this.elements.maskCanvas.getContext('2d');
        
        // Set initial brush size display
        this.updateBrushSizeDisplay();
        
        // Initialize responsive canvas
        this.initializeResponsiveCanvas();
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
            this.saveToLocalStorage();
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
            });
        }
        
        // Inpainting method selection
        document.querySelectorAll('input[name="inpainting_method"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.processingParams.inpainting_method = e.target.value;
                this.saveToLocalStorage();
            });
        });
        
        // Add resize handler for responsive canvas
        window.addEventListener('resize', () => {
            if (this.originalImage) {
                // Debounce the resize handler
                clearTimeout(this.resizeTimeout);
                this.resizeTimeout = setTimeout(() => {
                    this.displayImage(this.originalImage);
                    this.redrawMask();
                }, 250);
            }
        });
        
        // Load saved parameters on page load
        window.addEventListener('load', () => {
            this.updateAllValueDisplays();
        });
    }
    
    initializeResponsiveCanvas() {
        // Create a ResizeObserver to handle canvas container size changes
        if (typeof ResizeObserver !== 'undefined') {
            const canvasWrapper = document.getElementById('canvasWrapper');
            const resizeObserver = new ResizeObserver((entries) => {
                for (let entry of entries) {
                    if (this.originalImage && entry.target === canvasWrapper) {
                        // Debounce the resize handler
                        clearTimeout(this.resizeTimeout);
                        this.resizeTimeout = setTimeout(() => {
                            this.displayImage(this.originalImage);
                            this.redrawMask();
                        }, 250);
                    }
                }
            });
            
            // Start observing the canvas wrapper
            if (canvasWrapper) {
                resizeObserver.observe(canvasWrapper);
            }
        }
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
                
                // Initialize comparison slider
                this.initializeComparisonSlider();
            };
            img.src = e.target.result;
        };
        reader.onerror = () => {
            this.hideLoading();
            alert('Error reading file. Please try again.');
        };
        reader.readAsDataURL(file);
    }
    
    displayImage(img) {
        const canvas = this.elements.imageCanvas;
        const maskCanvas = this.elements.maskCanvas;
        const canvasWrapper = document.getElementById('canvasWrapper');
        
        if (!canvasWrapper) {
            console.error('Canvas wrapper not found');
            return;
        }
        
        // Get container dimensions
        const containerWidth = canvasWrapper.clientWidth;
        const containerHeight = canvasWrapper.clientHeight - 40; // Account for padding
        
        // Calculate image dimensions to fit within container while maintaining aspect ratio
        const maxWidth = Math.min(containerWidth, 1200);
        const maxHeight = Math.min(containerHeight, 600);
        
        let width = img.width;
        let height = img.height;
        
        // Calculate scaling ratio
        const scale = Math.min(maxWidth / width, maxHeight / height);
        
        // If image is larger than container, scale it down
        if (scale < 1) {
            width = Math.floor(width * scale);
            height = Math.floor(height * scale);
        }
        
        // Ensure minimum dimensions
        width = Math.max(width, 300);
        height = Math.max(height, 200);
        
        // Set canvas dimensions
        canvas.width = width;
        canvas.height = height;
        maskCanvas.width = width;
        maskCanvas.height = height;
        
        // Clear canvases
        this.imageCtx.clearRect(0, 0, width, height);
        this.maskCtx.clearRect(0, 0, width, height);
        
        // Draw image with crisp edges
        this.imageCtx.imageSmoothingEnabled = true;
        this.imageCtx.imageSmoothingQuality = 'high';
        this.imageCtx.drawImage(img, 0, 0, width, height);
        
        // Store display dimensions for coordinate mapping
        this.displayWidth = width;
        this.displayHeight = height;
        this.imageAspectRatio = img.width / img.height;
        this.canvasScale = scale;
        
        // Calculate centered position for canvas wrapper
        const wrapper = document.querySelector('.canvas-center-container');
        if (wrapper) {
            wrapper.style.width = `${width}px`;
            wrapper.style.height = `${height}px`;
        }
        
        // Store original image dimensions for backend processing
        this.originalWidth = img.width;
        this.originalHeight = img.height;
        
        // Reset mask data
        this.maskData = [];
        
        // Update brush size based on canvas scale
        this.brushSize = Math.max(10, 20 * scale);
        this.elements.brushSizeInput.value = this.brushSize;
        this.updateBrushSizeDisplay();
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
        const wrapper = document.querySelector('.canvas-center-container');
        
        if (!wrapper) {
            // Fallback to original calculation
            return {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
        }
        
        const wrapperRect = wrapper.getBoundingClientRect();
        
        // Calculate scale factor between canvas and display
        const scaleX = canvas.width / wrapperRect.width;
        const scaleY = canvas.height / wrapperRect.height;
        
        // Get position relative to wrapper (which is centered)
        const x = (e.clientX - wrapperRect.left) * scaleX;
        const y = (e.clientY - wrapperRect.top) * scaleY;
        
        // Clamp values to canvas bounds
        return {
            x: Math.max(0, Math.min(x, canvas.width)),
            y: Math.max(0, Math.min(y, canvas.height))
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
                    display_width: this.displayWidth,
                    display_height: this.displayHeight,
                    original_width: this.originalWidth,
                    original_height: this.originalHeight
                });
                formData.append('mask_data', maskData);
            }
            
            // Add processing parameters (simplified for new UI)
            const params = {
                inpainting_method: this.processingParams.inpainting_method,
                inpainting_radius: this.processingParams.inpainting_radius,
                gamma: this.processingParams.gamma,
                brush_size: this.brushSize
            };
            
            formData.append('parameters', JSON.stringify(params));
            
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
        if (result.metrics) {
            this.elements.processingTime.textContent = result.metrics.processing_time + 's';
            this.elements.psnrValue.textContent = result.metrics.psnr;
            this.elements.ssimValue.textContent = result.metrics.ssim;
            this.elements.improvementValue.textContent = result.metrics.improvement;
        } else {
            // Default values if metrics not provided
            this.elements.processingTime.textContent = '0.0';
            this.elements.psnrValue.textContent = '0.0';
            this.elements.ssimValue.textContent = '0.0';
            this.elements.improvementValue.textContent = '-';
        }
        
        // Store processed image data for download
        this.processedImageData = result.processed_image;
        this.processedFilename = result.filename;
        
        // Show results section
        this.elements.processingSection.style.display = 'none';
        this.elements.resultsSection.style.display = 'block';
        
        // Initialize comparison slider
        this.initializeComparisonSlider();
    }
    
    initializeComparisonSlider() {
        const slider = document.getElementById('comparisonSlider');
        const originalImg = this.elements.originalImage;
        const processedImg = this.elements.processedImage;
        
        if (!slider || !originalImg || !processedImg) return;
        
        slider.addEventListener('input', (e) => {
            const value = e.target.value;
            
            // Simple comparison effect
            originalImg.style.opacity = (100 - value) / 100;
            processedImg.style.opacity = value / 100;
        });
        
        // Reset on slider release
        slider.addEventListener('change', () => {
            setTimeout(() => {
                slider.value = 50;
                originalImg.style.opacity = 1;
                processedImg.style.opacity = 1;
            }, 300);
        });
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
        this.processedImageData = null;
        this.processedFilename = null;
        
        // Clear canvases
        if (this.displayWidth && this.displayHeight) {
            this.imageCtx.clearRect(0, 0, this.displayWidth, this.displayHeight);
            this.maskCtx.clearRect(0, 0, this.displayWidth, this.displayHeight);
        }
        
        // Reset mask data
        this.maskData = [];
        
        // Reset comparison slider
        const slider = document.getElementById('comparisonSlider');
        if (slider) {
            slider.value = 50;
        }
    }
    
    downloadProcessedImage() {
        if (!this.processedImageData) {
            alert('No processed image available to download');
            return;
        }
        
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
                const radio = document.querySelector(`input[name="inpainting_method"][value="${this.processingParams.inpainting_method}"]`);
                if (radio) {
                    radio.checked = true;
                }
                
                // Set slider values
                for (const [key, slider] of Object.entries(this.sliders)) {
                    if (slider && this.processingParams[key] !== undefined) {
                        slider.value = this.processingParams[key];
                    }
                }
                
            } catch (e) {
                console.error('Error loading saved data:', e);
                // Clear invalid data
                localStorage.removeItem('imageRestorationApp');
            }
        }
    }
}

// Initialize app when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ImageRestorationApp();
});