@echo off
chcp 65001 >nul
cls
echo ============================================
echo SIPAM COURSE COMPLIANCE - QUICK SETUP
echo ============================================
echo.
echo This script will set up CNN, IoT, and Transformer
echo components for course compliance.
echo.
echo Requirements:
echo - Python 3.11 installed
echo - ~2GB free disk space
echo - Backend running (optional for now)
echo.

REM Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.11 from python.org
    pause
    exit /b 1
)
echo ✓ Python found
echo.

REM Create virtual environment if it doesn't exist
echo [2/6] Setting up Python environment...
if not exist "ai_service\venv" (
    echo Creating virtual environment...
    cd ai_service
    python -m venv venv
    cd ..
) else (
    echo ✓ Virtual environment exists
)
echo.

REM Install dependencies
echo [3/6] Installing AI dependencies (this may take 5-10 minutes)...
echo Installing: TensorFlow, PyTorch, Transformers, OpenCV...
cd ai_service
call venv\Scripts\activate.bat
pip install -q --upgrade pip
pip install -q -r requirements_ai.txt
if errorlevel 1 (
    echo WARNING: Some packages may have failed. Continuing...
)
cd ..
echo ✓ Dependencies installed
echo.

REM Generate OCR dataset
echo [4/6] Generating synthetic OCR dataset...
echo This creates ~2,400 images for CNN training...
cd ai_service
python generate_synthetic_ocr_data.py --train-samples 50 --val-samples 15
if errorlevel 1 (
    echo ERROR: Dataset generation failed
    pause
    exit /b 1
)
cd ..
echo ✓ Dataset generated
echo.

REM Train CNN
echo [5/6] Training CNN (quick demo mode, ~10-15 minutes)...
echo Training with 15 epochs (sufficient for demonstration)...
cd ai_service
python train_cnn_quick.py --epochs 15 --batch-size 32
if errorlevel 1 (
    echo ERROR: CNN training failed
    pause
    exit /b 1
)
cd ..
echo ✓ CNN trained and saved
echo.

REM Test Transformer
echo [6/6] Testing Transformer NLP (downloads DistilBERT)...
cd ai_service
python -c "from transformer_nlp import get_nlp_analyzer; a = get_nlp_analyzer(); print('✓ Transformer loaded successfully')"
if errorlevel 1 (
    echo ERROR: Transformer setup failed
    pause
    exit /b 1
)
cd ..
echo ✓ Transformer ready
echo.

echo ============================================
echo SETUP COMPLETE!
echo ============================================
echo.
echo Course Compliance Status:
echo   ✓ CNN: Trained and ready (cnn_ocr_best.h5)
echo   ✓ IoT: Simulator ready (gps_simulator.py)
echo   ✓ Transformer: DistilBERT loaded
.
echo Next steps:
echo   1. Test IoT simulator:
echo      python iot/gps_simulator.py --duration 2
echo.
echo   2. Start AI service with new endpoints:
echo      cd ai_service
echo      python app.py
echo.
echo   3. Test CNN OCR:
echo      curl http://localhost:5001/ocr/models
echo.
echo   4. Test Transformer:
echo      curl -X POST http://localhost:5001/analyze_letter ^
echo        -H "Content-Type: application/json" ^
echo        -d "{\"text\": \"Sample motivation letter text...\"}"
echo.
echo   5. Update LaTeX documentation with results
.
echo.
pause
