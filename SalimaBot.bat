@echo off
title SalimaBot
echo Iniciando SalimaBot...
start "Ngrok" cmd /k ngrok http --domain=utter-earthly-spray.ngrok-free.dev 5000
timeout /t 3 /nobreak
start "" http://127.0.0.1:5000
python "C:\Users\salma\OneDrive - Educantabria\SalimaAI\proyecto\servidor.py"