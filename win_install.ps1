Write-Host "Creating virtual environment..."
python -m venv .venv

Write-Host "Activating virtual environment..."
.\.venv\Scripts\activate.ps1

Write-Host "Installing dependencies from win_requirements.txt..."
pip install -r win_requirements.txt

Write-Host "Installing Playwright Chromium..."
playwright install chromium

Write-Host "Setup complete!"