# Deployment Script for AI-Assisted Teaching System Backend

Write-Host "Starting Deployment..." -ForegroundColor Green

# 1. Check for Docker
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in the PATH."
    Write-Warning "Please install Docker Desktop for Windows: https://www.docker.com/products/docker-desktop/"
    Write-Warning "After installing, you may need to restart your terminal or computer."
    exit 1
}

# 2. Navigate to backend directory
Set-Location -Path "backend"

# 3. Build and Start Containers
Write-Host "Building and starting containers..." -ForegroundColor Cyan
docker-compose up -d --build

# 4. Wait for Database to be ready
Write-Host "Waiting for database to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# 5. Run Migrations
Write-Host "Running database migrations..." -ForegroundColor Cyan
docker-compose exec -T backend alembic upgrade head

# 6. Create Initial Data (Optional - e.g. Admin User)
# We could add a script for this, but for now we just notify.

Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "Backend is running at: http://localhost:8000"
Write-Host "API Documentation: http://localhost:8000/docs"
