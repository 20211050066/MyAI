"""启动入口"""
import subprocess
import sys


def main():
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"])


if __name__ == "__main__":
    main()
