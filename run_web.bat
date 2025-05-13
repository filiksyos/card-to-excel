@echo off
echo Starting Card to Excel Web Application...
cd web
set PYTHONPATH=%PYTHONPATH%;..
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 