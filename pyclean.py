from pathlib import Path
import shutil

if __name__ == '__main__':

    for dir in Path('.').rglob('__pycache__'):
        shutil.rmtree(dir.absolute(), True)
