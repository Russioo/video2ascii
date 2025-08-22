#!/usr/bin/env python3
"""
ASCII Video Converter Backend Starter
Tjekker dependencies og starter Flask server
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ er påkrævet")
        print(f"Du har Python {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_requirements():
    """Install required packages"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt ikke fundet")
        return False
    
    print("📦 Installerer Python packages...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Alle packages installeret successfully")
            return True
        else:
            print(f"❌ Package installation fejlede:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Fejl under package installation: {e}")
        return False

def check_dependencies():
    """Check if all dependencies are available"""
    required_packages = [
        ('cv2', 'opencv-python'),
        ('PIL', 'pillow'),
        ('numpy', 'numpy'),
        ('flask', 'flask'),
        ('flask_cors', 'flask-cors')
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} ikke fundet")
            missing_packages.append(package_name)
    
    # Check optional audio dependencies
    print("\nAudio support dependencies:")
    try:
        import moviepy
        print("✅ moviepy (audio support)")
    except ImportError:
        print("⚠ moviepy ikke fundet - prøver ffmpeg...")
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ ffmpeg (audio support)")
            else:
                print("❌ ffmpeg ikke fundet")
        except FileNotFoundError:
            print("❌ Ingen audio support tilgængelig")
    
    return len(missing_packages) == 0, missing_packages

def create_directories():
    """Create necessary directories"""
    dirs_to_create = ['uploads', 'outputs']
    
    for dir_name in dirs_to_create:
        dir_path = Path(__file__).parent / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"📁 {dir_name}/ directory klar")

def start_server():
    """Start the Flask server"""
    print("\n" + "="*50)
    print("🚀 Starter ASCII Video Converter Backend")
    print("="*50)
    
    app_file = Path(__file__).parent / "app.py"
    if not app_file.exists():
        print("❌ app.py ikke fundet")
        return False
    
    try:
        # Start Flask app
        os.system(f"python {app_file}")
        return True
    except KeyboardInterrupt:
        print("\n👋 Server stoppet")
        return True
    except Exception as e:
        print(f"❌ Server fejl: {e}")
        return False

def main():
    """Main function"""
    print("🎬 ASCII Video Converter Backend Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        input("Tryk Enter for at lukke...")
        return
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    
    if not deps_ok:
        print(f"\n❌ Manglende packages: {', '.join(missing)}")
        response = input("Vil du installere manglende packages? (y/n): ")
        
        if response.lower() in ['y', 'yes', 'ja']:
            if not install_requirements():
                input("Package installation fejlede. Tryk Enter for at lukke...")
                return
            
            # Re-check dependencies
            print("\nTjekker dependencies igen...")
            deps_ok, missing = check_dependencies()
            if not deps_ok:
                print(f"❌ Stadig manglende packages: {', '.join(missing)}")
                input("Tryk Enter for at lukke...")
                return
        else:
            print("❌ Kan ikke starte uden nødvendige packages")
            input("Tryk Enter for at lukke...")
            return
    
    # Create directories
    print("\nForbereder directories...")
    create_directories()
    
    # Start server
    print("\n✅ Alt er klar!")
    input("Tryk Enter for at starte server (Ctrl+C for at stoppe)...")
    start_server()

if __name__ == "__main__":
    main()

