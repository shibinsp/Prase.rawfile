@echo off
REM Windows batch file to run the EMS to PowerFactory Converter
REM 
REM Usage: run_converter.bat [input_file] [output_directory]
REM 
REM Examples:
REM   run_converter.bat my_ems_file.txt
REM   run_converter.bat my_ems_file.txt output_folder
REM   run_converter.bat my_ems_file.txt output_folder --verbose

echo ========================================
echo EMS to PowerFactory Converter
echo ========================================

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import pandas" >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing required packages...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install required packages!
        pause
        exit /b 1
    )
)

REM Set default values
set INPUT_FILE=%1
set OUTPUT_DIR=%2
set VERBOSE=%3

REM Check if input file is provided
if "%INPUT_FILE%"=="" (
    echo ERROR: Please provide an input file!
    echo.
    echo Usage: run_converter.bat [input_file] [output_directory]
    echo Example: run_converter.bat my_ems_file.txt output_folder
    pause
    exit /b 1
)

REM Check if input file exists
if not exist "%INPUT_FILE%" (
    echo ERROR: Input file "%INPUT_FILE%" does not exist!
    pause
    exit /b 1
)

REM Set default output directory if not provided
if "%OUTPUT_DIR%"=="" (
    set OUTPUT_DIR=output
)

REM Build the command
set COMMAND=python ems_to_powerfactory_converter.py "%INPUT_FILE%" -o "%OUTPUT_DIR%"

REM Add verbose flag if provided
if "%VERBOSE%"=="--verbose" (
    set COMMAND=%COMMAND% --verbose
)

echo.
echo Running converter with command:
echo %COMMAND%
echo.

REM Run the converter
%COMMAND%

REM Check if conversion was successful
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Conversion failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Conversion completed successfully!
echo ========================================
echo.
echo Output files are located in: %OUTPUT_DIR%
echo.
pause