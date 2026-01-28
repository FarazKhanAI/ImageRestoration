class ImageEditor {
    constructor() {
        this.imgElement = document.getElementById('restoredImage');
        this.canvas = document.getElementById('imageCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.editToggleBtn = document.getElementById('editToggleBtn');
        this.editPanel = document.getElementById('editPanel');
        this.downloadBtn = document.getElementById('downloadBtn');
        
        // Adjustment values
        this.adjustments = {
            brightness: 0,
            contrast: 0,
            temperature: 0,
            saturation: 0,
            enhancement: 0
        };
        
        // DOM elements for value displays
        this.valueDisplays = {
            brightness: document.getElementById('brightnessValue'),
            contrast: document.getElementById('contrastValue'),
            temperature: document.getElementById('temperatureValue'),
            saturation: document.getElementById('saturationValue'),
            enhancement: document.getElementById('enhancementValue')
        };
        
        // Original image data for resetting
        this.originalCanvasImageData = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateValueDisplays();
        
        // Pre-setup canvas when page loads
        this.preSetupCanvas();
    }
    
    bindEvents() {
        // Edit toggle button
        if (this.editToggleBtn) {
            this.editToggleBtn.addEventListener('click', () => this.toggleEditPanel());
        }
        
        // Close edit panel button
        const closeEditBtn = document.getElementById('closeEditBtn');
        if (closeEditBtn) {
            closeEditBtn.addEventListener('click', () => this.closeEditPanel());
        }
        
        // Download button
        if (this.downloadBtn) {
            this.downloadBtn.addEventListener('click', (e) => this.handleDownload(e));
        }
        
        // Reset button
        const resetBtn = document.getElementById('resetAdjustmentsBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetAdjustments());
        }
        
        // Adjustment sliders
        const sliderIds = ['brightness', 'contrast', 'temperature', 'saturation', 'enhancement'];
        
        sliderIds.forEach(sliderId => {
            const slider = document.getElementById(sliderId);
            if (slider) {
                slider.addEventListener('input', (e) => {
                    this.adjustments[sliderId] = parseInt(e.target.value);
                    this.valueDisplays[sliderId].textContent = this.adjustments[sliderId];
                    
                    // Update image in real-time
                    this.updateImage();
                });
            }
        });
    }
    
    preSetupCanvas() {
        // Wait for image to load first
        if (this.imgElement.complete) {
            this.initializeCanvas();
        } else {
            this.imgElement.addEventListener('load', () => {
                this.initializeCanvas();
            });
        }
    }
    
    initializeCanvas() {
        console.log('Initializing canvas with image...');
        
        // Get the actual displayed dimensions (not natural size)
        const displayWidth = this.imgElement.clientWidth;
        const displayHeight = this.imgElement.clientHeight;
        
        console.log('Display dimensions:', displayWidth, 'x', displayHeight);
        console.log('Natural dimensions:', this.imgElement.naturalWidth, 'x', this.imgElement.naturalHeight);
        
        // Set canvas to match displayed dimensions
        this.canvas.width = displayWidth;
        this.canvas.height = displayHeight;
        this.canvas.style.width = displayWidth + 'px';
        this.canvas.style.height = displayHeight + 'px';
        
        // Clear and draw the original image on canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.imgElement, 0, 0, displayWidth, displayHeight);
        
        // Store original canvas image data for resetting
        this.originalCanvasImageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        console.log('Canvas initialized with dimensions:', this.canvas.width, 'x', this.canvas.height);
    }
    
    toggleEditPanel() {
        if (this.editPanel.classList.contains('hidden')) {
            this.openEditPanel();
        } else {
            this.closeEditPanel();
        }
    }
    
    openEditPanel() {
        // First ensure canvas is properly set up
        if (!this.originalCanvasImageData) {
            this.initializeCanvas();
        }
        
        // Show edit panel
        this.editPanel.classList.remove('hidden');
        this.editToggleBtn.innerHTML = '<i class="fas fa-times"></i><span>Close Edit</span>';
        
        // Show canvas, hide original image
        this.canvas.style.display = 'block';
        this.imgElement.style.display = 'none';
        
        console.log('Edit panel opened - Canvas visible:', this.canvas.style.display);
    }
    
    closeEditPanel() {
        this.editPanel.classList.add('hidden');
        this.editToggleBtn.innerHTML = '<i class="fas fa-edit"></i><span>Edit Image</span>';
        
        // Show original image, hide canvas
        this.imgElement.style.display = 'block';
        this.canvas.style.display = 'none';
        
        // Reset to original image when closing
        this.resetToOriginal();
        
        console.log('Edit panel closed');
    }
    
    updateImage() {
        if (!this.canvas || this.canvas.width === 0 || this.canvas.height === 0) {
            console.error('Canvas not ready for update');
            return;
        }
        
        try {
            // Restore original image first
            if (this.originalCanvasImageData) {
                this.ctx.putImageData(this.originalCanvasImageData, 0, 0);
            }
            
            // Get current image data
            const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            const data = imageData.data;
            
            // Apply all adjustments
            this.applyAllAdjustments(data);
            
            // Put the modified image data back
            this.ctx.putImageData(imageData, 0, 0);
            
        } catch (error) {
            console.error('Error updating image:', error);
        }
    }
    
    applyAllAdjustments(data) {
        // Apply each adjustment in order
        this.applyBrightness(data);
        this.applyContrast(data);
        this.applyTemperature(data);
        this.applySaturation(data);
        this.applyEnhancement(data);
    }
    
    applyBrightness(data) {
        const brightness = this.adjustments.brightness;
        if (brightness === 0) return;
        
        const factor = brightness * 2.55; // Convert -100..100 to -255..255
        
        for (let i = 0; i < data.length; i += 4) {
            data[i] = this.clamp(data[i] + factor, 0, 255);     // R
            data[i + 1] = this.clamp(data[i + 1] + factor, 0, 255); // G
            data[i + 2] = this.clamp(data[i + 2] + factor, 0, 255); // B
        }
    }
    
    applyContrast(data) {
        const contrast = this.adjustments.contrast;
        if (contrast === 0) return;
        
        // Better contrast formula
        const factor = (259 * (contrast + 255)) / (255 * (259 - contrast));
        
        for (let i = 0; i < data.length; i += 4) {
            data[i] = this.clamp(factor * (data[i] - 128) + 128, 0, 255);     // R
            data[i + 1] = this.clamp(factor * (data[i + 1] - 128) + 128, 0, 255); // G
            data[i + 2] = this.clamp(factor * (data[i + 2] - 128) + 128, 0, 255); // B
        }
    }
    
    applyTemperature(data) {
        const temp = this.adjustments.temperature;
        if (temp === 0) return;
        
        for (let i = 0; i < data.length; i += 4) {
            let r = data[i];
            let g = data[i + 1];
            let b = data[i + 2];
            
            if (temp > 0) {
                // Warm: increase red, decrease blue
                r += temp * 2.55;
                b -= temp * 1.275;
            } else {
                // Cool: increase blue, decrease red
                const coolFactor = Math.abs(temp);
                r -= coolFactor * 1.275;
                b += coolFactor * 2.55;
            }
            
            data[i] = this.clamp(r, 0, 255);
            data[i + 1] = this.clamp(g, 0, 255);
            data[i + 2] = this.clamp(b, 0, 255);
        }
    }
    
    applySaturation(data) {
        const saturation = this.adjustments.saturation / 100;
        if (Math.abs(saturation) < 0.01) return;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Calculate grayscale value
            const gray = 0.299 * r + 0.587 * g + 0.114 * b;
            
            // Apply saturation
            const newR = gray + (r - gray) * (1 + saturation);
            const newG = gray + (g - gray) * (1 + saturation);
            const newB = gray + (b - gray) * (1 + saturation);
            
            data[i] = this.clamp(newR, 0, 255);
            data[i + 1] = this.clamp(newG, 0, 255);
            data[i + 2] = this.clamp(newB, 0, 255);
        }
    }
    
    applyEnhancement(data) {
        const enhancement = this.adjustments.enhancement;
        if (enhancement === 0) return;
        
        // Enhancement combines multiple effects
        const factor = 1 + (enhancement * 0.01);
        
        for (let i = 0; i < data.length; i += 4) {
            // Simple enhancement: boost contrast and vibrance
            data[i] = this.clamp(128 + (data[i] - 128) * factor, 0, 255);     // R
            data[i + 1] = this.clamp(128 + (data[i + 1] - 128) * factor, 0, 255); // G
            data[i + 2] = this.clamp(128 + (data[i + 2] - 128) * factor, 0, 255); // B
        }
    }
    
    clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }
    
    resetAdjustments() {
        // Reset all slider values
        this.adjustments = {
            brightness: 0,
            contrast: 0,
            temperature: 0,
            saturation: 0,
            enhancement: 0
        };
        
        // Update sliders
        document.getElementById('brightness').value = 0;
        document.getElementById('contrast').value = 0;
        document.getElementById('temperature').value = 0;
        document.getElementById('saturation').value = 0;
        document.getElementById('enhancement').value = 0;
        
        // Update value displays
        this.updateValueDisplays();
        
        // Reset canvas to original image
        this.resetToOriginal();
    }
    
    resetToOriginal() {
        if (this.originalCanvasImageData) {
            this.ctx.putImageData(this.originalCanvasImageData, 0, 0);
        } else if (this.imgElement.complete) {
            // Re-draw original image if no stored data
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.drawImage(this.imgElement, 0, 0, this.canvas.width, this.canvas.height);
        }
    }
    
    updateValueDisplays() {
        for (const key in this.valueDisplays) {
            if (this.valueDisplays[key]) {
                this.valueDisplays[key].textContent = this.adjustments[key];
            }
        }
    }
    
    async handleDownload(e) {
        e.preventDefault();
        
        try {
            // Show loading
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
            }
            
            let imageUrl;
            let filename;
            
            if (!this.editPanel.classList.contains('hidden')) {
                // Using edited image from canvas
                imageUrl = this.canvas.toDataURL('image/jpeg', 0.95);
                filename = `edited_${this.getFilename()}.jpg`;
            } else {
                // Using original restored image
                imageUrl = this.imgElement.src;
                filename = this.getFilename();
            }
            
            // Download the image
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Hide loading
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
            
        } catch (error) {
            console.error('Download error:', error);
            alert('Failed to download image. Please try again.');
            
            // Hide loading on error
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    }
    
    getFilename() {
        // Extract filename from session info or use default
        const filenameElement = document.querySelector('.filename');
        if (filenameElement) {
            const originalName = filenameElement.textContent;
            // Remove extension and add timestamp
            const nameWithoutExt = originalName.replace(/\.[^/.]+$/, '');
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-');
            return `${nameWithoutExt}_restored_${timestamp}.jpg`;
        }
        return `restored_image_${Date.now()}.jpg`;
    }
}

// Initialize image editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize image editor immediately
    window.imageEditor = new ImageEditor();
    console.log('Image editor initialized');
});