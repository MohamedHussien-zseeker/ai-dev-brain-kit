# Brain CLI — Windows installer (no admin required)
# Usage:
#   powershell -c "Invoke-WebRequest -Uri https://github.com/owner/repo/releases/latest/download/install.ps1 -OutFile install.ps1; .\install.ps1"
#   .\install.ps1 -Version v0.1.0 -InstallDir "$env:USERPROFILE\brain"

param(
    [string]$Version = "v0.1.0",
    [string]$InstallDir = "$env:USERPROFILE\AppData\Local\Programs\brain",
    [string]$Repo = "MohamedHussien-zseeker/ai-dev-brain-kit",
    [switch]$NoVerify
)

$ErrorActionPreference = "Stop"
Write-Host "=== Brain CLI Installer ===" -ForegroundColor Green

# Step 1: Detect architecture
$arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else {
    Write-Host "ERROR: 32-bit Windows is not supported." -ForegroundColor Red
    exit 1
}

$binaryName = "brain-windows-$arch.exe"
$binaryUrl = "https://github.com/$Repo/releases/download/$Version/$binaryName"
$checksumUrl = "$binaryUrl.sha256"
$installPath = Join-Path $InstallDir "brain.exe"

# Step 2: Create install directory
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Write-Host "Install target: $InstallDir" -ForegroundColor Green

# Step 3: Download binary
Write-Host "Downloading $binaryName ..."
try {
    Invoke-WebRequest -Uri $binaryUrl -OutFile $installPath -UseBasicParsing
} catch {
    Write-Host "ERROR: Download failed. Check version and network." -ForegroundColor Red
    exit 1
}
Write-Host "Downloaded: $installPath" -ForegroundColor Green
Write-Host "Size: $((Get-Item $installPath).Length / 1MB) MB" -ForegroundColor Green

# Step 4: Verify checksum
if (-not $NoVerify) {
    Write-Host "Verifying SHA-256 ..."
    try {
        $expected = (Invoke-WebRequest -Uri $checksumUrl -UseBasicParsing).Content.Trim().Split(' ')[0]
        $actual = (Get-FileHash -Path $installPath -Algorithm SHA256).Hash.ToLower()
        if ($expected -ne $actual) {
            Write-Host "ERROR: Checksum mismatch!" -ForegroundColor Red
            Write-Host "  Expected: $expected" -ForegroundColor Red
            Write-Host "  Actual:   $actual" -ForegroundColor Red
            Remove-Item $installPath -Force
            exit 1
        }
        Write-Host "Checksum verified: $actual" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Could not fetch checksum; skipping verification." -ForegroundColor Yellow
    }
}

# Step 5: Create config directory (preserve existing)
$configDir = "$env:USERPROFILE\.brain"
New-Item -ItemType Directory -Force -Path $configDir | Out-Null
$configPath = Join-Path $configDir "config.json"
if (-not (Test-Path $configPath)) {
    @{
        version = 1
        vaultPath = ""
        provider = "openai-compatible"
        baseUrl = ""
        model = ""
        captureMode = "approval-required"
    } | ConvertTo-Json | Set-Content $configPath
    Write-Host "Default config created at $configPath" -ForegroundColor Green
} else {
    Write-Host "Existing config preserved at $configPath" -ForegroundColor Green
}

# Step 6: Add to PATH (user-level, no admin)
$pathScope = "User"
$currentPath = [Environment]::GetEnvironmentVariable("PATH", $pathScope)
if ($currentPath -notlike "*$InstallDir*") {
    $newPath = "$currentPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, $pathScope)
    Write-Host "Added $InstallDir to user PATH" -ForegroundColor Green
    Write-Host "Restart your terminal or run: `$env:PATH = `"`$env:PATH;$InstallDir`"" -ForegroundColor Yellow
} else {
    Write-Host "$InstallDir already in PATH" -ForegroundColor Green
}

# Step 7: Verify
if (-not $NoVerify) {
    Write-Host "Verifying installation ..." -ForegroundColor Green
    try {
        $version = & $installPath --version
        Write-Host $version -ForegroundColor Green
        & $installPath doctor --offline
    } catch {
        Write-Host "WARNING: Binary at $installPath but verification failed." -ForegroundColor Yellow
    }
}

Write-Host "`nInstallation complete. Run these to get started:" -ForegroundColor Green
Write-Host "  brain --version" -ForegroundColor Cyan
Write-Host "  brain doctor --offline" -ForegroundColor Cyan
Write-Host "  brain init" -ForegroundColor Cyan
Write-Host "  brain note 'your quick thought'" -ForegroundColor Cyan
Write-Host "  brain today" -ForegroundColor Cyan
