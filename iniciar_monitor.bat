@echo off
title Job Monitor 3D - Vigilante de Ofertas
cd /d "C:\Users\Josep\Documents\GitHub\Portfolio"
echo ======================================================
echo    INICIANDO JOB MONITOR 3D (ALERTAS EN TELEGRAM)
echo ======================================================
echo.
echo Monitorizando ofertas de arte 3D, props y entornos...
echo Deja esta ventana minimizada para recibir alertas 24/7.
echo.
python job_monitor.py
pause
