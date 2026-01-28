class ImageEditor {
    constructor() {
        this.originalImage = null;
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
        this.undoStack = [];
        this.redoStack = [];
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.isPanning = false;
        this.lastPanX = 0;
        this.lastPanY = 0;
        this.strokeCount = 0;
        
        // Updated processing parameters
        this.processingParams = {
            gamma: 1.0,
            inpainting_method: 'hybrid',
            inpainting_radius: 3,
            brush_size: 20
        };
        
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.canvasContainer = document.getElementById('canvasContainer');
        
        this.initializeElements();
        this.bindEvents();
        this.loadImage();
        this.loadFromLocalStorage();
    }
    
    initializeElements() {
        // Get DOM elements
        this.elements = {
            imageCanvas: document.getElementById('imageCanvas'),
            maskCanvas: document.getElementById('maskCanvas'),
            brushSizeInput: document.getElementById('brushSize'),
            brushSizeValue: document.getElementById('brushSizeValue'),
            currentBrushSize: document.getElementById('currentBrushSize'),
            clearBtn: document.getElementById('clearBtn'),
            undoBtn: document.getElementById('undoBtn'),
            changeImageBtn: document.getElementById('changeImageBtn'),
            processBtn: document.getElementById('processBtn'),
            inpaintingMethod: document.getElementById('inpaintingMethod'),
            inpaintingRadius: document.getElementById('inpaintingRadius'),
            inpaintingRadiusValue: document.getElementById('inpaintingRadiusValue'),
            gamma: document.getElementById('gamma'),
            gammaValue: document.getElementById('gammaValue')
        };
        
        // Initialize canvas contexts
        this.imageCtx = this.elements.imageCanvas.getContext('2d');
        this.maskCtx = this.elements.maskCanvas.getContext('2d');
        
        // Set initial brush size display
        this.updateBrushSizeDisplay();
    }
    
    bindEvents() {
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
        
        // Canvas panning
        this.elements.imageCanvas.addEventListener('wheel', (e) => this.handleWheel(e));
        this.elements.imageCanvas.addEventListener('mousedown', (e) => {
            if (e.button === 1 || e.button === 2) { // Middle or right click
                e.preventDefault();
                this.startPanning(e);
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (this.isPanning) {
                this.pan(e);
            }
        });
        
        document.addEventListener('mouseup', (e) => {
            if (this.isPanning) {
                this.stopPanning();
            }
        });
        
        // Prevent context menu on canvas
        this.elements.imageCanvas.addEventListener('contextmenu', (e) => e.preventDefault());
        
        // Mask controls
        this.elements.clearBtn.addEventListener('click', () => this.clearMask());
        this.elements.undoBtn.addEventListener('click', () => this.undo());
        
        // Change Image button
        this.elements.changeImageBtn.addEventListener('click', () => this.changeImage());
        
        // Processing button
        this.elements.processBtn.addEventListener('click', () => this.processImage());
        
        // Slider events
        this.elements.inpaintingRadius.addEventListener('input', (e) => {
            this.processingParams.inpainting_radius = parseInt(e.target.value);
            this.elements.inpaintingRadiusValue.textContent = e.target.value;
            this.saveToLocalStorage();
        });
        
        this.elements.gamma.addEventListener('input', (e) => {
            this.processingParams.gamma = parseFloat(e.target.value);
            this.elements.gammaValue.textContent = parseFloat(e.target.value).toFixed(2);
            this.saveToLocalStorage();
        });
        
        // Inpainting method selection (dropdown)
        this.elements.inpaintingMethod.addEventListener('change', (e) => {
            this.processingParams.inpainting_method = e.target.value;
            this.saveToLocalStorage();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+Z for undo
            if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                this.undo();
            }
            // Ctrl+Y or Ctrl+Shift+Z for redo
            else if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'Z')) {
                e.preventDefault();
                this.redo();
            }
            // Plus/Minus for brush size
            else if (e.key === '+' || e.key === '=') {
                e.preventDefault();
                this.elements.brushSizeInput.value = Math.min(100, parseInt(this.elements.brushSizeInput.value) + 5);
                this.brushSize = parseInt(this.elements.brushSizeInput.value);
                this.updateBrushSizeDisplay();
            }
            else if (e.key === '-' || e.key === '_') {
                e.preventDefault();
                this.elements.brushSizeInput.value = Math.max(5, parseInt(this.elements.brushSizeInput.value) - 5);
                this.brushSize = parseInt(this.elements.brushSizeInput.value);
                this.updateBrushSizeDisplay();
            }
        });
        
        // Window resize handler
        window.addEventListener('resize', () => {
            if (this.originalImage) {
                this.fitImageToCanvas();
            }
        });
    }
    
    loadImage() {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        // Get image URL from the page data
        const imageUrl = document.querySelector('meta[name="image-url"]');
        if (imageUrl && imageUrl.content) {
            img.src = imageUrl.content;
        } else {
            // Fallback: try to get image from canvas or data attribute
            const canvas = document.getElementById('imageCanvas');
            if (canvas && canvas.dataset.imageUrl) {
                img.src = canvas.dataset.imageUrl;
            } else {
                console.error('No image URL found');
                alert('Failed to load image. Please try uploading again.');
                window.location.href = '/';
                return;
            }
        }
        
        img.onload = () => {
            this.originalImage = img;
            this.fitImageToCanvas();
        };
        
        img.onerror = () => {
            console.error('Failed to load image');
            alert('Failed to load image. Please try uploading again.');
            window.location.href = '/';
        };
    }
    
    fitImageToCanvas() {
        const canvas = this.elements.imageCanvas;
        const maskCanvas = this.elements.maskCanvas;
        const container = this.canvasContainer;
        
        if (!container || !this.originalImage) return;
        
        // Get container dimensions
        const containerWidth = container.clientWidth - 40; // Account for padding
        const containerHeight = container.clientHeight - 40;
        
        // Calculate image dimensions to fit container
        const imgWidth = this.originalImage.width;
        const imgHeight = this.originalImage.height;
        
        // Calculate scale to fit container
        const scaleX = containerWidth / imgWidth;
        const scaleY = containerHeight / imgHeight;
        this.scale = Math.min(scaleX, scaleY, 1); // Don't scale up
        
        // Calculate canvas dimensions
        const canvasWidth = imgWidth * this.scale;
        const canvasHeight = imgHeight * this.scale;
        
        // Set canvas dimensions
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;
        maskCanvas.width = canvasWidth;
        maskCanvas.height = canvasHeight;
        
        // Calculate centering offsets
        this.offsetX = (containerWidth - canvasWidth) / 2;
        this.offsetY = (containerHeight - canvasHeight) / 2;
        
        // Position canvases
        const canvasCenter = canvas.parentElement;
        canvasCenter.style.width = `${canvasWidth}px`;
        canvasCenter.style.height = `${canvasHeight}px`;
        canvasCenter.style.margin = `${this.offsetY}px ${this.offsetX}px`;
        
        // Clear and draw image
        this.imageCtx.clearRect(0, 0, canvasWidth, canvasHeight);
        this.imageCtx.drawImage(this.originalImage, 0, 0, canvasWidth, canvasHeight);
        
        // Clear mask
        this.maskCtx.clearRect(0, 0, canvasWidth, canvasHeight);
        
        // Redraw existing mask if any
        this.redrawMask();
    }
    
    getCanvasPosition(e) {
        const canvas = this.elements.imageCanvas;
        const rect = canvas.getBoundingClientRect();
        const canvasCenter = canvas.parentElement;
        const centerRect = canvasCenter.getBoundingClientRect();
        
        // Calculate position relative to centered canvas
        const scaleX = canvas.width / centerRect.width;
        const scaleY = canvas.height / centerRect.height;
        
        const x = (e.clientX - centerRect.left) * scaleX;
        const y = (e.clientY - centerRect.top) * scaleY;
        
        // Clamp values to canvas bounds
        return {
            x: Math.max(0, Math.min(x, canvas.width)),
            y: Math.max(0, Math.min(y, canvas.height))
        };
    }
    
    startDrawing(e) {
        this.isDrawing = true;
        const pos = this.getCanvasPosition(e);
        this.lastX = pos.x;
        this.lastY = pos.y;
        
        // Save state for undo
        this.saveState();
        
        // Draw initial point
        this.drawPoint(pos.x, pos.y);
        this.maskData.push({x: pos.x, y: pos.y});
        this.strokeCount++;
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
        if (this.isDrawing) {
            this.isDrawing = false;
            this.saveToLocalStorage();
        }
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
    
    updateBrushSizeDisplay() {
        this.elements.brushSizeValue.textContent = this.brushSize;
        this.processingParams.brush_size = this.brushSize;
    }
    
    clearMask() {
        if (this.maskData.length === 0) return;
        
        if (confirm('Are you sure you want to clear all marks?')) {
            this.saveState();
            this.maskCtx.clearRect(0, 0, this.elements.maskCanvas.width, this.elements.maskCanvas.height);
            this.maskData = [];
            this.strokeCount = 0;
            this.saveToLocalStorage();
        }
    }
    
    undo() {
        if (this.undoStack.length === 0) return;
        
        // Save current state to redo stack
        const currentState = this.maskCtx.getImageData(0, 0, 
            this.elements.maskCanvas.width, 
            this.elements.maskCanvas.height);
        this.redoStack.push({
            imageData: currentState,
            maskData: [...this.maskData],
            strokeCount: this.strokeCount
        });
        
        // Restore previous state
        const previousState = this.undoStack.pop();
        this.maskCtx.putImageData(previousState.imageData, 0, 0);
        this.maskData = previousState.maskData;
        this.strokeCount = previousState.strokeCount;
        this.saveToLocalStorage();
    }
    
    redo() {
        if (this.redoStack.length === 0) return;
        
        // Save current state to undo stack
        const currentState = this.maskCtx.getImageData(0, 0, 
            this.elements.maskCanvas.width, 
            this.elements.maskCanvas.height);
        this.undoStack.push({
            imageData: currentState,
            maskData: [...this.maskData],
            strokeCount: this.strokeCount
        });
        
        // Restore next state
        const nextState = this.redoStack.pop();
        this.maskCtx.putImageData(nextState.imageData, 0, 0);
        this.maskData = nextState.maskData;
        this.strokeCount = nextState.strokeCount;
        this.saveToLocalStorage();
    }
    
    saveState() {
        const imageData = this.maskCtx.getImageData(0, 0, 
            this.elements.maskCanvas.width, 
            this.elements.maskCanvas.height);
        
        this.undoStack.push({
            imageData: imageData,
            maskData: [...this.maskData],
            strokeCount: this.strokeCount
        });
        
        // Clear redo stack when new action is performed
        this.redoStack = [];
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
    
    handleWheel(e) {
        e.preventDefault();
        
        if (e.ctrlKey) {
            // Zoom with Ctrl + Scroll
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.scale = Math.max(0.1, Math.min(this.scale * delta, 3));
            this.fitImageToCanvas();
        }
    }
    
    startPanning(e) {
        this.isPanning = true;
        this.lastPanX = e.clientX;
        this.lastPanY = e.clientY;
        this.elements.imageCanvas.style.cursor = 'grabbing';
    }
    
    pan(e) {
        if (!this.isPanning) return;
        
        const deltaX = e.clientX - this.lastPanX;
        const deltaY = e.clientY - this.lastPanY;
        
        this.offsetX += deltaX;
        this.offsetY += deltaY;
        
        // Clamp offsets to keep canvas in view
        const maxOffset = 100;
        this.offsetX = Math.max(-maxOffset, Math.min(this.offsetX, maxOffset));
        this.offsetY = Math.max(-maxOffset, Math.min(this.offsetY, maxOffset));
        
        const canvasCenter = this.elements.imageCanvas.parentElement;
        canvasCenter.style.margin = `${this.offsetY}px ${this.offsetX}px`;
        
        this.lastPanX = e.clientX;
        this.lastPanY = e.clientY;
    }
    
    stopPanning() {
        this.isPanning = false;
        this.elements.imageCanvas.style.cursor = 'crosshair';
    }
    
    changeImage() {
        if (confirm('Are you sure you want to change the image? All current marks will be lost.')) {
            window.location.href = '/';
        }
    }
    
    async processImage() {
        if (!this.originalImage) {
            alert('Please upload an image first');
            return;
        }
        
        this.showLoading('Processing image...');
        
        try {
            // Prepare form data
            const formData = new FormData();
            
            // Add mask data if exists
            if (this.maskData.length > 0) {
                const maskData = JSON.stringify({
                    coordinates: this.maskData,
                    brush_size: this.brushSize,
                    display_width: this.elements.imageCanvas.width,
                    display_height: this.elements.imageCanvas.height
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
                // Redirect to results page
                window.location.href = result.redirect || '/results';
            } else {
                throw new Error(result.error || 'Processing failed');
            }
            
        } catch (error) {
            console.error('Processing error:', error);
            alert('Error processing image: ' + error.message);
            this.hideLoading();
        }
    }
    
    showLoading(message = 'Processing...') {
        if (this.loadingOverlay) {
            const messageEl = this.loadingOverlay.querySelector('h3');
            if (messageEl && message) {
                messageEl.textContent = message;
            }
            this.loadingOverlay.style.display = 'flex';
        }
    }
    
    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }
    
    saveToLocalStorage() {
        const data = {
            processingParams: this.processingParams,
            maskData: this.maskData,
            brushSize: this.brushSize,
            strokeCount: this.strokeCount
        };
        localStorage.setItem('imageRestorationEditor', JSON.stringify(data));
    }
    
    loadFromLocalStorage() {
        const saved = localStorage.getItem('imageRestorationEditor');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                this.processingParams = {...this.processingParams, ...data.processingParams};
                this.maskData = data.maskData || [];
                this.brushSize = data.brushSize || 20;
                this.strokeCount = data.strokeCount || 0;
                
                // Update UI elements
                this.elements.brushSizeInput.value = this.brushSize;
                this.updateBrushSizeDisplay();
                
                // Set dropdown value
                if (this.elements.inpaintingMethod) {
                    this.elements.inpaintingMethod.value = this.processingParams.inpainting_method || 'hybrid';
                }
                
                // Set slider values
                this.elements.inpaintingRadius.value = this.processingParams.inpainting_radius || 3;
                this.elements.inpaintingRadiusValue.textContent = this.processingParams.inpainting_radius || 3;
                
                this.elements.gamma.value = this.processingParams.gamma || 1.0;
                this.elements.gammaValue.textContent = (this.processingParams.gamma || 1.0).toFixed(2);
                
            } catch (e) {
                console.error('Error loading saved data:', e);
            }
        }
    }
}

// Initialize editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.imageEditor = new ImageEditor();
});