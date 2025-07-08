# AI EPUB Rewriter - Premium GUI Edition

A stunning, luxury graphical interface for the AI_epub_edits tool, featuring a modern dark theme with gold accents, dynamic backgrounds, and glassmorphism effects.

![Premium GUI Preview](assets/gui_preview.png)

## ✨ Features

### 🎨 **Aesthetic Design**
- **Modern Luxury Theme**: Deep charcoal backgrounds with metallic gold accents
- **Dynamic Animated Background**: Reactive gradients that smoothly transition between screens
- **Glassmorphism Effects**: Semi-transparent panels with frosted glass appearance
- **Premium Typography**: Elegant fonts with perfect contrast for readability

### 🔧 **Core Functionality**
- **Project Management**: Create, browse, and manage multiple EPUB rewriting projects
- **Real-time Processing**: Watch your chapters being rewritten with live progress updates
- **Intelligent Configuration**: Easy access to AI provider settings and processing options
- **One-Click Packaging**: Export your rewritten EPUBs with a single button

### 🚀 **User Experience**
- **Fluid Animations**: Smooth transitions and hover effects throughout
- **Responsive Design**: Scales beautifully on different screen sizes
- **Intuitive Navigation**: Clear workflow from project creation to final EPUB
- **Real-time Feedback**: Processing logs and progress indicators keep you informed

## 📋 Requirements

- Python 3.8 or higher
- All dependencies from the main tool
- Additional GUI dependencies (included in requirements.txt)

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the GUI**
   ```bash
   python run_gui.py
   # or
   ./run_gui.py
   ```

## 🎮 How to Use

### Home Screen
The welcome screen presents two main options:
- **Create New Project**: Start a fresh EPUB rewriting project
- **Browse Projects**: View and manage existing projects

### Creating a Project
1. Click "Create New Project"
2. Enter a unique project name
3. Select your source EPUB file
4. Choose a style reference text file
5. Click "Create Project"

### Processing Your EPUB
1. Open a project from the Projects screen
2. Configure chapter range (optional)
3. Click "Start Processing"
4. Monitor progress in real-time
5. Package the final EPUB when complete

### Settings
Access the settings screen to configure:
- AI Provider (OpenAI, Gemini, AIStudio)
- API Keys
- Model selection
- Processing limits

## 🎨 Design Philosophy

The interface embodies a **"Modern Luxury"** aesthetic:

- **Color Palette**:
  - Primary: Deep Charcoal (#1E1E1E)
  - Accent: Metallic Gold (#C89B3C)
  - Text: Creamy Off-white (#F0E6D2)

- **Visual Effects**:
  - Animated gradient backgrounds
  - Glass morphism panels
  - Smooth hover animations
  - Reactive color transitions

## 🏗️ Architecture

The GUI is built with:
- **Kivy**: For the core application framework
- **Custom Shaders**: For the animated background and glass effects
- **Async Processing**: Background threads for non-blocking operations
- **Modular Screens**: Clean separation of UI components

### File Structure
```
gui_app.py          # Main application and background effects
gui_screens.py      # All screen implementations
gui_layout.kv       # Visual styling definitions
run_gui.py          # Quick launcher script
```

## 🔧 Customization

### Changing Colors
Edit the color definitions in `gui_layout.kv`:
```kivy
#:set GOLD [0.784, 0.608, 0.235, 1]
#:set LIGHT_GOLD [0.941, 0.902, 0.824, 1]
```

### Modifying Animations
Adjust animation parameters in `gui_app.py`:
```python
def transition_to_theme(self, theme_name, duration=1.5):
    # Modify duration for faster/slower transitions
```

## 🐛 Troubleshooting

### GUI Won't Start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ required)
- Verify Kivy installation

### Performance Issues
- The animated background requires GPU acceleration
- Try reducing shader complexity if needed
- Close other GPU-intensive applications

### Visual Glitches
- Update graphics drivers
- Try different Kivy window providers
- Disable compositor effects on Linux

## 📝 Notes

- The GUI maintains full compatibility with the CLI tool
- Projects created in either interface are interchangeable
- All processing happens through the same backend
- Settings are shared between GUI and CLI

## 🎯 Future Enhancements

- [ ] Theme customization options
- [ ] Live chapter preview during processing
- [ ] Batch project management
- [ ] Export statistics and analytics
- [ ] Built-in style reference editor

---

*Experience the future of EPUB rewriting with our premium interface.*