@echo off
setlocal

set "FORK_URL=https://github.com/ZiChuanShanFeng/VCPToolBox.git"
set "BRANCH_NAME=master"

echo ==================================================
echo      Upload to Fork Script
echo ==================================================
echo.
echo This script will commit all local changes and push them
echo to the '%BRANCH_NAME%' branch of your forked repository.
echo.
echo  - Fork URL: %FORK_URL%
echo  - Target Branch: %BRANCH_NAME%
echo.

:: Check for git
git --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Git is not installed or not in your system's PATH.
    echo Please install Git and try again.
    goto :eof
)

:: Check if the current directory is a git repository
git rev-parse --is-inside-work-tree >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: This is not a Git repository.
    echo Please run "git init" first.
    goto :eof
)

echo Step 1: Configuring the remote for your fork...
git remote get-url myfork >nul 2>nul
if %errorlevel% neq 0 (
    echo Adding new remote "myfork".
    git remote add myfork %FORK_URL%
) else (
    echo Updating existing remote "myfork".
    git remote set-url myfork %FORK_URL%
)
if %errorlevel% neq 0 (
    echo Error: Failed to configure the remote repository.
    goto :eof
)
echo.

echo Step 2: Switching to the '%BRANCH_NAME%' branch...
git checkout %BRANCH_NAME% >nul 2>nul
if %errorlevel% neq 0 (
    echo '%BRANCH_NAME%' branch does not exist. Creating it...
    git checkout -b %BRANCH_NAME%
)
echo.

echo Step 3: Staging all files for commit (including new, modified, and deleted files)...
git add -A
echo.

echo Step 4: Committing all staged files...
set "commit_message=chore: Sync local changes"
git commit -m "%commit_message%"
if %errorlevel% neq 0 (
    echo Warning: Commit failed. This might be because there are no changes to commit.
    echo Aborting push.
    goto :eof
)
echo.

echo Step 5: Pushing to the '%BRANCH_NAME%' branch on your fork...
git push --force myfork %BRANCH_NAME%
if %errorlevel% neq 0 (
    echo Error: Failed to push the branch to the remote repository.
    goto :eof
)
echo.

echo ==================================================
echo      Successfully pushed to your fork!
echo ==================================================
echo.