# 📁 Connecting to Your GitHub Repository

Here's how to connect your existing local project to your GitHub repository:

## **Step-by-Step Git Setup**

### **1. Initialize Git in Your Project**
```bash
# Navigate to your project folder
cd F:\DIP_project\image-restoration-app

# Initialize git repository
git init
```

### **2. Connect to Your GitHub Repository**
```bash
# Add your GitHub repository as remote origin
git remote add origin https://github.com/FarazKhanAI/ImageRestoration.git

# Verify the remote URL
git remote -v
```

### **3. Configure Git (Set Your Identity)**
```bash
# Set your name and email (use your GitHub credentials)
git config --global user.name "FarazKhanAI"
git config --global user.email "your-email@example.com"
```

## **📁 Create a Proper .gitignore File**

Create a new `.gitignore` file in your project root with this content:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Instance folder (uploads, processed images)
instance/uploads/
instance/processed/

# IDE
.vscode/
.idea/
*.swp
*.swo
*.sublime-*

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Temp files
*.tmp
*.temp

# Environment variables
.env
.flaskenv
.secrets

# Database
*.db
*.sqlite3

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
ENV/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/
```

## **📦 Prepare Your First Commit**

```bash
# Check what files will be added
git status

# Stage all files (except those in .gitignore)
git add .

# Check staged files
git status

# Create your first commit
git commit -m "Initial commit: Complete Image Restoration Flask App with OpenCV backend"

# Check commit history
git log --oneline
```

## **🚀 Push to GitHub**

```bash
# Push to GitHub (main branch)
git push -u origin main

# If you get an error about the branch not existing, use:
git branch -M main
git push -u origin main

# Or if your default branch is master:
git push -u origin master
```

## **🛠️ Troubleshooting Common Issues**

### **Issue 1: Repository already exists**
```bash
# If you get "origin already exists", remove it first:
git remote remove origin
git remote add origin https://github.com/FarazKhanAI/ImageRestoration.git
```

### **Issue 2: Rejected push due to unrelated histories**
```bash
# Pull and merge with unrelated histories
git pull origin main --allow-unrelated-histories

# If conflicts occur, resolve them, then:
git add .
git commit -m "Merge remote repository"
git push origin main
```

### **Issue 3: Permission denied**
```bash
# For HTTPS authentication issues, use personal access token
# Go to GitHub → Settings → Developer Settings → Personal Access Tokens
# Create token with repo permissions

# Then use token in URL:
git remote set-url origin https://YOUR_TOKEN@github.com/FarazKhanAI/ImageRestoration.git
```

## **📋 Quick Command Reference**

| Command | Purpose |
|---------|---------|
| `git init` | Initialize git repository |
| `git remote add origin <url>` | Add GitHub repository |
| `git remote -v` | Verify remote URL |
| `git add .` | Stage all changes |
| `git commit -m "message"` | Commit changes |
| `git push origin main` | Push to GitHub |
| `git status` | Check repository status |
| `git log --oneline` | View commit history |

## **🔐 Set Up GitHub Authentication**

### **Method A: HTTPS with Credential Helper (Recommended)**
```bash
# Cache credentials for 1 hour
git config --global credential.helper cache
git config --global credential.helper 'cache --timeout=3600'

# Push and enter username/password when prompted
git push origin main
```

### **Method B: SSH Key Authentication**
```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key
cat ~/.ssh/id_rsa.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key

# Change remote to SSH URL
git remote set-url origin git@github.com:FarazKhanAI/ImageRestoration.git
```

## **📁 Project Files to Upload**

Here's what will be uploaded to GitHub:

```
ImageRestoration/
├── app.py
├── config.py
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── backend/
│   ├── __init__.py
│   ├── image_processor.py
│   ├── enhancement.py
│   ├── scratch_removal.py
│   ├── utils.py
│   └── validators.py
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/
├── templates/
│   ├── base.html
│   └── index.html
└── instance/
    ├── .gitkeep    # Empty file to keep folder
    ├── uploads/
    │   └── .gitkeep
    └── processed/
        └── .gitkeep
```

## **📝 Create a .env.example File**

Create `/.env.example` (don't upload `.env` itself):

```env
# Environment Variables Template
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-this
DEBUG=True
MAX_CONTENT_LENGTH=16777216
```

## **✅ Final Setup Commands**

Run these commands in order:

```bash
# 1. Navigate to project
cd F:\DIP_project\image-restoration-app

# 2. Initialize git
git init

# 3. Add remote
git remote add origin https://github.com/FarazKhanAI/ImageRestoration.git

# 4. Create .gitignore (copy content above)
# 5. Create .env.example (copy content above)

# 6. Create .gitkeep files for empty folders
echo "" > instance/.gitkeep
echo "" > instance/uploads/.gitkeep  
echo "" > instance/processed/.gitkeep

# 7. Stage files
git add .

# 8. Commit
git commit -m "Initial commit: Complete Image Restoration App with Flask + OpenCV"

# 9. Push to GitHub
git push -u origin main

# If main branch doesn't exist:
git branch -M main
git push -u origin main
```

## **🔍 Verify Upload**

After pushing, check your GitHub repository:
1. Go to https://github.com/FarazKhanAI/ImageRestoration
2. You should see all your files
3. The README.md should display properly

## **🔄 Daily Workflow**

For regular development:

```bash
# Check status
git status

# Add changes
git add .

# Commit with descriptive message
git commit -m "Fixed: Updated validation logic for parameters"

# Push to GitHub
git push origin main

# Pull latest changes (if collaborating)
git pull origin main
```

## **🎯 Success Checklist**

- [ ] Git initialized locally
- [ ] GitHub repository connected
- [ ] `.gitignore` file created
- [ ] `.env.example` created (without real secrets)
- [ ] All project files staged
- [ ] First commit created
- [ ] Code pushed to GitHub
- [ ] Repository visible on GitHub.com
- [ ] README.md displays correctly

## **🚨 Important Notes**

1. **Never commit `.env` file** with real passwords/keys
2. **Never commit large files** (>100MB)
3. **Keep `instance/` folder in .gitignore** (except .gitkeep)
4. **Use meaningful commit messages**
5. **Push regularly** to backup your work

Your project is now version-controlled and backed up on GitHub! 🎉
