@echo off
rem ============================================================
rem  Builds the Controls Standard and one PDF per appendix.
rem  Double-click this file in the Controls Standard folder.
rem  Output:
rem    Controls Standard rev-<rev>.pdf
rem    Appendix PDFs\Controls Standard rev-<rev> - Appendix <X> - <Title>.pdf
rem  The revision letter is read from revision.tex.
rem ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set REV=
for /f "tokens=3 delims={}" %%r in ('findstr "documentrevision" revision.tex') do set REV=%%r
if "%REV%"=="" (
  echo Could not read the revision letter from revision.tex
  pause
  exit /b 1
)
echo Building Controls Standard rev-%REV% ...

if not exist build mkdir build
if not exist "Appendix PDFs" mkdir "Appendix PDFs"

rem ---- Full document (three passes for contents and cross-references)
for /l %%i in (1,1,3) do pdflatex -interaction=nonstopmode "Controls Standard.tex" >nul
if not exist "Controls Standard.pdf" (
  echo The main document did not build. Open "Controls Standard.log" to see why.
  pause
  exit /b 1
)
copy /y "Controls Standard.pdf" "Controls Standard rev-%REV%.pdf" >nul
copy /y "Controls Standard.aux" "build\master-refs.aux" >nul
echo   Controls Standard rev-%REV%.pdf

rem ---- Standalone appendices
for %%f in (standalone\appendix-*.tex) do (
  if /i not "%%~nf"=="appendix-common" (
    pdflatex -interaction=nonstopmode -output-directory=build "%%f" >nul
    pdflatex -interaction=nonstopmode -output-directory=build "%%f" >nul
    if exist "build\%%~nf.name" (
      set /p NAME=<"build\%%~nf.name"
      copy /y "build\%%~nf.pdf" "Appendix PDFs\!NAME!.pdf" >nul
      echo   Appendix PDFs\!NAME!.pdf
    ) else (
      echo   %%~nf did not build. See build\%%~nf.log
    )
  )
)

echo.
echo Done.
pause
