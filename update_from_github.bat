@echo off
setlocal

set "REPO_URL=https://github.com/lioensky/VCPToolBox.git"
set "TEMP_DIR=%TEMP%\vcp_update"

echo ==================================================
echo      VCP Self-Host Update Script
echo ==================================================
echo.
echo This script will update your local folder with new files
echo from the VCPToolBox repository without overwriting
echo or deleting any of your existing files.
echo.

:: Check for git
git --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Git is not installed or not in your system's PATH.
    echo Please install Git and try again.
    goto :eof
)

echo Step 1: Cleaning up any previous temporary update folders...
if exist "%TEMP_DIR%" (
    rmdir /s /q "%TEMP_DIR%"
)
echo.

echo Step 2: Cloning the latest repository into a temporary folder...
git clone --depth 1 %REPO_URL% "%TEMP_DIR%"
if %errorlevel% neq 0 (
    echo Error: Failed to clone the repository.
    echo Please check your internet connection and the repository URL.
    goto :cleanup
)
echo.

echo Step 3: Copying new files only. Existing files will be skipped.
echo Source: %TEMP_DIR%
echo Destination: %CD%
echo.
robocopy "%TEMP_DIR%" "%CD%" /E /XC /XN /XO /XD .git
echo.

echo Step 4: Update complete.
echo.

:cleanup
echo Step 5: Deleting temporary folder...
if exist "%TEMP_DIR%" (
    rmdir /s /q "%TEMP_DIR%"
)
echo.

echo ==================================================
echo      Update process finished.
echo ==================================================
echo.
pause
