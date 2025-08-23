# DynamoDB Local Startup Script
# Manages Docker Compose services for Simple Cloud Kit Database Testing

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "clean", "admin", "tools")]
    [string]$Action = "start",
    [switch]$Detached = $true,
    [switch]$WithAdmin,
    [switch]$WithTools,
    [switch]$Follow,
    [string]$Service = $null
)

# Set location to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Simple Cloud Kit - DynamoDB Local Manager" -ForegroundColor Green
Write-Host "=" * 50

# Check if Docker is running
function Test-DockerRunning {
    try {
        docker version | Out-Null
        return $true
    } catch {
        Write-Host "ERROR: Docker is not running or not installed" -ForegroundColor Red
        Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
        return $false
    }
}

# Check if Docker Compose is available
function Test-DockerCompose {
    try {
        docker-compose version | Out-Null
        return $true
    } catch {
        try {
            docker compose version | Out-Null
            return $true
        } catch {
            Write-Host "ERROR: Docker Compose is not available" -ForegroundColor Red
            return $false
        }
    }
}

# Get the appropriate Docker Compose command
function Get-DockerComposeCmd {
    try {
        docker-compose version | Out-Null
        return "docker-compose"
    } catch {
        return "docker compose"
    }
}

# Create data directory if it doesn't exist
function Initialize-DataDirectory {
    $dataDir = Join-Path $ScriptDir "dynamodb-data"
    if (-not (Test-Path $dataDir)) {
        Write-Host "Creating data directory: $dataDir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    }
}

# Main script logic
if (-not (Test-DockerRunning)) {
    exit 1
}

if (-not (Test-DockerCompose)) {
    exit 1
}

$dockerComposeCmd = Get-DockerComposeCmd
Write-Host "Using: $dockerComposeCmd" -ForegroundColor Cyan

# Build compose command
$composeArgs = @()
if ($WithTools) {
    $composeArgs += "--profile", "tools"
}

switch ($Action.ToLower()) {
    "start" {
        Write-Host "Starting DynamoDB Local services..." -ForegroundColor Yellow
        
        Initialize-DataDirectory
        
        $services = @("dynamodb-local")
        if ($WithAdmin) {
            $services += "dynamodb-admin"
        }
        
        $startArgs = $composeArgs + @("up")
        if ($Detached) {
            $startArgs += "-d"
        }
        $startArgs += $services
        
        & $dockerComposeCmd @startArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "Services started successfully!" -ForegroundColor Green
            Write-Host "DynamoDB Local: http://localhost:8000" -ForegroundColor Cyan
            if ($WithAdmin) {
                Write-Host "DynamoDB Admin: http://localhost:8001" -ForegroundColor Cyan
            }
            Write-Host ""
            Write-Host "Test connection with:" -ForegroundColor Yellow
            Write-Host "  .\view.ps1" -ForegroundColor White
            Write-Host ""
            Write-Host "Useful commands:" -ForegroundColor Yellow
            Write-Host "  .\start.ps1 status    - Check service status" -ForegroundColor White
            Write-Host "  .\start.ps1 logs      - View logs" -ForegroundColor White
            Write-Host "  .\start.ps1 stop      - Stop services" -ForegroundColor White
        }
    }
    
    "stop" {
        Write-Host "Stopping DynamoDB Local services..." -ForegroundColor Yellow
        & $dockerComposeCmd @composeArgs down
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Services stopped successfully!" -ForegroundColor Green
        }
    }
    
    "restart" {
        Write-Host "Restarting DynamoDB Local services..." -ForegroundColor Yellow
        & $dockerComposeCmd @composeArgs restart $Service
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Services restarted successfully!" -ForegroundColor Green
        }
    }
    
    "status" {
        Write-Host "Service Status:" -ForegroundColor Yellow
        & $dockerComposeCmd @composeArgs ps
        
        Write-Host ""
        Write-Host "Container Health:" -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -UseBasicParsing
            Write-Host "✓ DynamoDB Local: Healthy (HTTP $($response.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "✗ DynamoDB Local: Unhealthy ($($_.Exception.Message))" -ForegroundColor Red
        }
        
        if ($WithAdmin) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8001/" -TimeoutSec 5 -UseBasicParsing
                Write-Host "✓ DynamoDB Admin: Healthy (HTTP $($response.StatusCode))" -ForegroundColor Green
            } catch {
                Write-Host "✗ DynamoDB Admin: Unhealthy ($($_.Exception.Message))" -ForegroundColor Red
            }
        }
    }
    
    "logs" {
        Write-Host "Viewing logs..." -ForegroundColor Yellow
        $logArgs = $composeArgs + @("logs")
        if ($Follow) {
            $logArgs += "-f"
        }
        if ($Service) {
            $logArgs += $Service
        }
        
        & $dockerComposeCmd @logArgs
    }
    
    "clean" {
        Write-Host "Cleaning up DynamoDB Local data and containers..." -ForegroundColor Yellow
        Write-Host "WARNING: This will delete all data!" -ForegroundColor Red
        
        $confirm = Read-Host "Are you sure? (y/N)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            & $dockerComposeCmd @composeArgs down -v --remove-orphans
            
            $dataDir = Join-Path $ScriptDir "dynamodb-data"
            if (Test-Path $dataDir) {
                Write-Host "Removing data directory..." -ForegroundColor Yellow
                Remove-Item -Path $dataDir -Recurse -Force
            }
            
            Write-Host "Cleanup completed!" -ForegroundColor Green
        } else {
            Write-Host "Cleanup cancelled" -ForegroundColor Yellow
        }
    }
    
    "admin" {
        Write-Host "Starting with DynamoDB Admin UI..." -ForegroundColor Yellow
        & $MyInvocation.MyCommand.Path -Action start -WithAdmin
    }
    
    "tools" {
        Write-Host "Starting with all tools..." -ForegroundColor Yellow
        & $MyInvocation.MyCommand.Path -Action start -WithAdmin -WithTools
    }
    
    default {
        Write-Host "Usage: .\start.ps1 [action] [options]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Cyan
        Write-Host "  start     Start DynamoDB Local (default)" -ForegroundColor White
        Write-Host "  stop      Stop all services" -ForegroundColor White
        Write-Host "  restart   Restart services" -ForegroundColor White
        Write-Host "  status    Show service status and health" -ForegroundColor White
        Write-Host "  logs      Show service logs" -ForegroundColor White
        Write-Host "  clean     Stop services and remove all data" -ForegroundColor White
        Write-Host "  admin     Start with Admin UI" -ForegroundColor White
        Write-Host "  tools     Start with all tools" -ForegroundColor White
        Write-Host ""
        Write-Host "Options:" -ForegroundColor Cyan
        Write-Host "  -WithAdmin    Include DynamoDB Admin UI" -ForegroundColor White
        Write-Host "  -WithTools    Include AWS CLI tools" -ForegroundColor White
        Write-Host "  -Follow       Follow logs (for logs action)" -ForegroundColor White
        Write-Host "  -Service      Target specific service" -ForegroundColor White
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Cyan
        Write-Host "  .\start.ps1                    # Start DynamoDB Local only" -ForegroundColor White
        Write-Host "  .\start.ps1 admin              # Start with Admin UI" -ForegroundColor White
        Write-Host "  .\start.ps1 start -WithAdmin   # Start with Admin UI" -ForegroundColor White
        Write-Host "  .\start.ps1 logs -Follow       # Follow logs" -ForegroundColor White
        Write-Host "  .\start.ps1 status             # Check health" -ForegroundColor White
        Write-Host "  .\start.ps1 clean              # Clean everything" -ForegroundColor White
    }
}
