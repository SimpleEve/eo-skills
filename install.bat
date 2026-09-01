@echo off
setlocal EnableExtensions EnableDelayedExpansion

if "%~1"=="-h" (
  goto :usage
) else if "%~1"=="--help" (
  goto :usage
) else if not "%~1"=="" (
  echo 未知参数: %~1（无 per-agent 旗标；未检测到的 agent 自动跳过）
  goto :usage_error
)

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1}"

set "SHARED_DIR=%USERPROFILE%\.agents\skills"
set "FOUND=0"
for /D %%D in ("%SCRIPT_DIR%\eo-*") do (
  if /I not "%%~nxD"=="eo-doc" set "FOUND=1"
)

if "!FOUND!"=="0" (
  echo 未找到任何 eo-* skill 目录，请确认脚本位于仓库根目录。
  exit /b 1
)

call :link_into_shared || exit /b 1

if exist "%USERPROFILE%\.claude" call :link_agent ".claude" "Claude" || exit /b 1
if exist "%USERPROFILE%\.codex" call :link_agent ".codex" "Codex" || exit /b 1
if exist "%USERPROFILE%\.gemini\antigravity" call :link_agent ".gemini\antigravity" "Antigravity" || exit /b 1

echo 安装完成。
echo 提示: eo-* CLI (eo-helper / eo-board / eo-sync 及其适配器) 暂不支持 Windows 原生安装 (eo-sync 的并发锁依赖 POSIX fcntl)，可在 WSL 下用 install.sh 接线。
exit /b 0

::link_into_shared — junction 到跨 agent 标准位
:link_into_shared
if not exist "%SHARED_DIR%" mkdir "%SHARED_DIR%"

for /D %%D in ("%SCRIPT_DIR%\eo-*") do (
  if /I not "%%~nxD"=="eo-doc" (
    set "SKILL_NAME=%%~nxD"
    set "TARGET_PATH=%SHARED_DIR%\!SKILL_NAME!"

    if exist "!TARGET_PATH!" (
      echo [shared] 跳过 !SKILL_NAME!，目标已存在: !TARGET_PATH!
    ) else (
      mklink /J "!TARGET_PATH!" "%%~fD" >nul
      if errorlevel 1 (
        echo [shared] 创建链接失败: !SKILL_NAME!
        exit /b 1
      )

      echo [shared] 已链接 !SKILL_NAME! ^> !TARGET_PATH!
    )
  )
)

exit /b 0

::link_agent — 在检测到的 agent skills 目录建链指向标准位
:link_agent
set "AGENT_DIR=%~1"
set "AGENT_NAME=%~2"
set "AGENT_SKILLS_DIR=%USERPROFILE%\%AGENT_DIR%\skills"

if not exist "%AGENT_SKILLS_DIR%" mkdir "%AGENT_SKILLS_DIR%"

for /D %%D in ("%SCRIPT_DIR%\eo-*") do (
  if /I not "%%~nxD"=="eo-doc" (
    set "SKILL_NAME=%%~nxD"
    set "TARGET_PATH=%AGENT_SKILLS_DIR%\!SKILL_NAME!"

    if exist "!TARGET_PATH!" (
      echo [!AGENT_NAME!] 跳过 !SKILL_NAME!，目标已存在: !TARGET_PATH!
    ) else (
      mklink /J "!TARGET_PATH!" "%SHARED_DIR%\!SKILL_NAME!" >nul
      if errorlevel 1 (
        echo [!AGENT_NAME!] 创建链接失败: !SKILL_NAME!
        exit /b 1
      )

      echo [!AGENT_NAME!] 已链接 !SKILL_NAME! ^> !TARGET_PATH!
    )
  )
)

exit /b 0

:usage
echo 用法:
echo   install.bat
echo.
echo 说明:
echo   把仓库下所有 eo-* skill junction 到跨 agent 标准位
echo   %%USERPROFILE%%\.agents\skills，再在检测到的 agent 目录各建链:
echo   - %%USERPROFILE%%\.claude\skills              (Claude Code)
echo   - %%USERPROFILE%%\.codex\skills               (Codex)
echo   - %%USERPROFILE%%\.gemini\antigravity\skills  (Antigravity)
echo   与 skills CLI（npx skills add）落位同构；目标已有同名条目时跳过不覆盖。
exit /b 0

:usage_error
echo.
echo 可用参数:
echo   -h
echo   --help
exit /b 1
