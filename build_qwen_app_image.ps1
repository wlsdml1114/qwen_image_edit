param(
    [Parameter(Mandatory = $true)]
    [string]$RuntimeImage,

    [Parameter(Mandatory = $true)]
    [string]$AppImage
)

$ErrorActionPreference = 'Stop'

if ($RuntimeImage -notmatch '@sha256:[0-9a-fA-F]{64}$') {
    throw 'RuntimeImage must be an immutable registry reference ending in @sha256:<64 hex characters>.'
}
if ($AppImage -match '\s' -or $AppImage -notmatch '^[^:]+/.+:.+$') {
    throw 'AppImage must be a registry/repository:tag reference.'
}

$workerRoot = $PSScriptRoot
$dockerExe = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerExe) {
    throw 'Docker CLI is missing. Install Docker Desktop and start its Linux container engine.'
}

Push-Location $workerRoot
try {
    & $dockerExe.Source buildx build `
        --file Dockerfile.app `
        --build-arg "QWEN_RUNTIME_IMAGE=$RuntimeImage" `
        --tag $AppImage `
        --push `
        .
    if ($LASTEXITCODE -ne 0) {
        throw "Qwen app image build/push failed with exit code $LASTEXITCODE. The live endpoint was not changed."
    }
} finally {
    Pop-Location
}

Write-Output "APP_IMAGE_PUBLISHED=$AppImage"
Write-Output 'NEXT: configure a staging Runpod Serverless endpoint to use this image and verify image-count workflows before production.'
