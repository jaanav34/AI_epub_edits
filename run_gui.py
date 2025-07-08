#!/usr/bin/env python3
"""
AI EPUB Rewriter - Premium GUI Launcher
Quick launcher script for the premium graphical interface
"""

import sys
import os

# Ensure the GUI dependencies are available
try:
    import kivy
    from kivy import require
    require('2.2.0')
except ImportError:
    print("Error: Kivy is not installed.")
    print("Please install the GUI dependencies with:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

# Import and run the GUI application
try:
    from gui_app import PremiumEbookRewriterApp
    
    if __name__ == '__main__':
        # Create app instance and run
        app = PremiumEbookRewriterApp()
        app.run()
        
except Exception as e:
    print(f"Error launching GUI: {e}")
    print("\nPlease ensure all dependencies are installed:")
    print("  pip install -r requirements.txt")
    sys.exit(1)