import sys
import subprocess
import os

def check_mdict():
    print(f"Python executable: {sys.executable}")
    cmd = [sys.executable, '-m', 'mdict_utils', '--help']
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        if result.returncode == 0:
            print("mdict-utils is available!")
            return True
        else:
            print(f"mdict-utils error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    check_mdict()
