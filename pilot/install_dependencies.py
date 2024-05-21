import subprocess
import sys

def install_package(package):
    try:
        __import__(package)
    except ImportError:
        print(f"{package} not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    else:
        print(f"{package} is already installed")

if __name__ == "__main__":
    install_package("networkx")
    install_package("astor")