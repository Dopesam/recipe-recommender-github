@echo off
echo Starting Recipe Recommender App...
echo.
echo Opening in your default browser in 5 seconds...
echo.

:: Change to the app directory
cd /d "C:\Users\Admin\recipe-recommender"

:: Start the Flask app in the background
start /B python run_app.py

:: Wait 5 seconds for the server to start
timeout /t 5 /nobreak >nul

:: Open the app in default browser
start http://localhost:5000

echo.
echo ✅ App is running at http://localhost:5000
echo.
echo Press any key to stop the app and close this window...
pause >nul

:: Kill the Python process when done
taskkill /f /im python.exe 2>nul
exit
