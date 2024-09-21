$ErrorActionPreference = "Stop"

function Write-ErrorMessage {
    param([string]$message)
    Write-Host $message -ForegroundColor Red
    exit 1
}

try {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment" }

    Write-Host "Activating virtual environment..."
    .\.venv\Scripts\activate.ps1
    if ($LASTEXITCODE -ne 0) { throw "Failed to activate virtual environment" }

    Write-Host "Installing dependencies from win_requirements.txt..."
    pip install -r win_requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Failed to install dependencies" }

    Write-Host "Installing Playwright Chromium..."
    playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw "Failed to install Playwright Chromium" }

    Write-Host "Setting up .env configuration file..."
    python .\install\setup_env.py
    if ($LASTEXITCODE -ne 0) { throw "Failed to set up .env configuration file" }

    Write-Host "Setup complete!"
}
catch {
    Write-ErrorMessage "An error occurred during setup: $_"
}