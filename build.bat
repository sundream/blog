@echo off

pyinstaller -F ./gen_sidebar.py
mv dist/gen_sidebar.exe .
rmdir /S /Q dist
rmdir /S /Q build
rm gen_sidebar.spec

pause