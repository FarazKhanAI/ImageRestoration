class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('themeToggle');
        this.themeIcon = this.themeToggle.querySelector('i');
        this.themeText = this.themeToggle.querySelector('.theme-text');
        this.currentTheme = localStorage.getItem('theme') || 'light';
        
        this.init();
    }
    
    init() {
        // Apply saved theme with a slight delay to allow DOM to load
        setTimeout(() => {
            this.applyTheme(this.currentTheme);
        }, 100);
        
        // Bind event listener
        this.themeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleTheme();
        });
        
        // Add keyboard support
        this.themeToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }
    
    applyTheme(theme) {
        // Start transition
        document.body.style.transition = 'all 0.3s ease';
        
        // Remove all theme classes
        document.body.classList.remove('light-mode', 'dark-mode');
        
        // Add new theme class
        document.body.classList.add(`${theme}-mode`);
        
        // Update storage
        localStorage.setItem('theme', theme);
        this.currentTheme = theme;
        
        // Update button
        this.updateButton();
        
        // Dispatch custom event for other components
        const themeChangeEvent = new CustomEvent('themeChanged', { detail: { theme } });
        document.dispatchEvent(themeChangeEvent);
    }
    
    toggleTheme() {
        // Add animation class for smooth transition
        document.body.classList.add('theme-transitioning');
        
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        
        // Add a slight delay for better UX
        setTimeout(() => {
            this.applyTheme(newTheme);
            document.body.classList.remove('theme-transitioning');
        }, 50);
    }
    
    updateButton() {
        const icon = this.themeIcon;
        const text = this.themeText;
        
        if (this.currentTheme === 'dark') {
            // Smooth icon transition
            icon.style.transition = 'transform 0.3s ease';
            icon.style.transform = 'rotate(360deg)';
            
            setTimeout(() => {
                icon.className = 'fas fa-sun';
                icon.style.transform = 'rotate(0deg)';
                text.textContent = 'Light Mode';
                this.themeToggle.setAttribute('aria-label', 'Switch to light mode');
                this.themeToggle.setAttribute('title', 'Switch to light mode');
            }, 150);
        } else {
            // Smooth icon transition
            icon.style.transition = 'transform 0.3s ease';
            icon.style.transform = 'rotate(360deg)';
            
            setTimeout(() => {
                icon.className = 'fas fa-moon';
                icon.style.transform = 'rotate(0deg)';
                text.textContent = 'Dark Mode';
                this.themeToggle.setAttribute('aria-label', 'Switch to dark mode');
                this.themeToggle.setAttribute('title', 'Switch to dark mode');
            }, 150);
        }
    }
    
    // Public method to get current theme
    getCurrentTheme() {
        return this.currentTheme;
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
    
    // Add smooth transition for all elements
    const style = document.createElement('style');
    style.textContent = `
        .theme-transitioning * {
            transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease !important;
        }
        
        /* Accessibility improvements */
        .theme-toggle:focus {
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }
    `;
    document.head.appendChild(style);
});