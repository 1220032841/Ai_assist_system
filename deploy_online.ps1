Write-Host "Starting online deployment..." -ForegroundColor Green

if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH."
    exit 1
}

Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".env.online")) {
    Write-Warning ".env.online not found. Creating from .env.online.example"
    Copy-Item ".env.online.example" ".env.online"
    Write-Warning "Please edit .env.online first, then run this script again."
    exit 1
}

$llmKeyLine = Get-Content ".env.online" | Where-Object { $_ -match '^\s*LLM_API_KEY\s*=' } | Select-Object -First 1
$llmApiKey = ""
if ($llmKeyLine) {
    $llmApiKey = ($llmKeyLine -split "=", 2)[1].Trim()
}
if (-not $llmApiKey) {
    Write-Warning "LLM_API_KEY is empty in .env.online. AI feedback generation will fail until this is configured."
}

docker compose -f docker-compose.online.yml --env-file .env.online up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Build startup failed. Trying cached images with --no-build..."
    docker compose -f docker-compose.online.yml --env-file .env.online up -d --no-build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start services."
        Write-Warning "If logs mention docker.m.daocloud.io or image metadata pull failure, check Docker mirror settings and network DNS."
        exit 1
    }
}

Write-Host "Running migrations..." -ForegroundColor Cyan
docker compose -f docker-compose.online.yml --env-file .env.online exec -T backend alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Error "Migration failed."
    exit 1
}

Write-Host "Online deployment completed." -ForegroundColor Green
Write-Host "Open http://<your-server-public-ip>/ from student and teacher devices."
Write-Host "For production, bind a domain and enable HTTPS."
