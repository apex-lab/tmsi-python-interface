call py -3.10 --version
if %errorlevel% neq 0 exit /b %errorlevel%
call py -3.10 -m venv .venv_310_beta
call .\.venv_310_beta\Scripts\activate
call pip install -r .\requirements310_Windows.txt
echo --------------------------------------
echo installation successfully completed
pause >nul