@echo off
chcp 65001 >nul
echo ============================================
echo   Oracle Sales AI - Setup Automatico
echo ============================================
echo.

echo Instalando dependencias...
pip install streamlit pandas anthropic python-dateutil

echo.
echo Dependencias instaladas!
echo.

echo Iniciando aplicacao...
echo.

streamlit run app.py

pause