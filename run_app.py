#!/usr/bin/env python3
"""
Recipe Recommender Web Application
A global recipe discovery platform with search, voice search, and favorites functionality.
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    return True

def install_requirements():
    """Install required Python packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Packages installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        return False

def run_application():
    """Start the Flask application"""
    print("\n🍳 Starting Recipe Recommender Server...")
    print("🌐 Open your browser and navigate to: http://localhost:5000")
    print("🔹 Features included:")
    print("   • Recipe search and filtering")
    print("   • Voice search functionality")
    print("   • 'Surprise Me' random recipe selection")
    print("   • Favorites management")
    print("   • Detailed recipe information with health benefits")
    print("   • Animated food backgrounds")
    print("\n⚡ Press Ctrl+C to stop the server\n")
    
    # Change to backend directory and run the Flask app
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    try:
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thanks for using Recipe Recommender!")

def main():
    """Main function to set up and run the application"""
    print("🍳 Recipe Recommender Setup")
    print("=" * 50)
    
    if not check_python_version():
        return
    
    if not install_requirements():
        return
    
    run_application()

if __name__ == '__main__':
    main()
