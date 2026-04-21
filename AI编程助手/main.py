import subprocess
import sys


def main():
    """启动Streamlit应用"""
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])


if __name__ == '__main__':
    main()
