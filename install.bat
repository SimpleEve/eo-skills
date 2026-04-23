@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "INSTALL_CLAUDE=1"
set "INSTALL_CODEX=1"
set "INSTALL_ANTIGRAVITY=1"

if /I "%~1"=="--claude-only" (
  set "INSTALL_CODEX=0"
  set "INSTALL_ANTIGRAVITY=0"
  shift
) else if /I "%~1"=="--codex-only" (
  set "INSTALL_CLAUDE=0"
  set "INSTALL_ANTIGRAVITY=0"
  shift
) else if /I "%~1"=="--antigravity-only" (
  set "INSTALL_CLAUDE=0"
  set "INSTALL_CODEX=0"
  shift
) else if /I "%~1"=="-h" (
  goto :usage
) else if /I "%~1"=="--help" (
  goto :usage
) else if not "%~1"=="" (
  echo 未知参数: %~1
  goto :usage_error
)

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "FOUND=0"
for /D %%D in ("%SCRIPT_DIR%\eo-*") do (
  set "FOUND=1"
)

if "!FOUND!"=="0" (
  echo 未找到任何 eo-* skill 目录，请确认脚本位于仓库根目录。
  exit /b 1
)

if "%INSTALL_CLAUDE%"=="1" call :link_skills "%USERPROFILE%\.claude\skills" "Claude" || exit /b 1
if "%INSTALL_CODEX%"=="1" call :link_skills "%USERPROFILE%\.agents\skills" "Codex" || exit /b 1
if "%INSTALL_ANTIGRAVITY%"=="1" call :link_skills "%USERPROFILE%\.gemini\antigravity\skills" "Antigravity" || exit /b 1

echo 安装完成。
echo 提示: eo-flow 依赖 tmux + smux 提供的 tmux-bridge；如果只用单 agent 流，可以先不装。
exit /b 0

:link_skills
set "TARGET_DIR=%~1"
set "TARGET_NAME=%~2"

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

for /D %%D in ("%SCRIPT_DIR%\eo-*") do (
  set "SKILL_NAME=%%~nxD"
  set "TARGET_PATH=%TARGET_DIR%\!SKILL_NAME!"

  if exist "!TARGET_PATH!" (
    echo [!TARGET_NAME!] 跳过 !SKILL_NAME!，目标已存在: !TARGET_PATH!
  ) else (
    mklink /J "!TARGET_PATH!" "%%~fD" >nul
    if errorlevel 1 (
      echo [!TARGET_NAME!] 创建链接失败: !SKILL_NAME!
      exit /b 1
    )

    echo [!TARGET_NAME!] 已链接 !SKILL_NAME! ^> !TARGET_PATH!
  )
)

exit /b 0

:usage
echo 用法:
echo   install.bat
echo   install.bat --claude-only
echo   install.bat --codex-only
echo   install.bat --antigravity-only
echo.
echo 说明:
echo   默认同时把当前仓库下所有 eo-* skill 直接链接到:
echo   - %%USERPROFILE%%\.claude\skills              (Claude Code)
echo   - %%USERPROFILE%%\.agents\skills              (Codex)
echo   - %%USERPROFILE%%\.gemini\antigravity\skills  (Antigravity)
exit /b 0

:usage_error
echo.
echo 可用参数:
echo   --claude-only
echo   --codex-only
echo   --antigravity-only
echo   -h
echo   --help
exit /b 1
