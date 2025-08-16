import os

os.system("pyinstaller python-prints.py --onedir --name python-prints --hidden-import=win32timezone --clean --exclude-module tkinter --exclude-module test --exclude-module distutils")