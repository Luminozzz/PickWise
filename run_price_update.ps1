$ProjectRoot = "c:\Users\nicho\OneDrive\Documents\Orbital\PickWise"
$LogFile     = "$ProjectRoot\logs\price_update.log"

Set-Location $ProjectRoot

New-Item -ItemType Directory -Force -Path "$ProjectRoot\logs" | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "`n[$timestamp] Starting add_new_product_price"

$env:PYTHONPATH = "$ProjectRoot;$ProjectRoot\backend"

$result = & "C:\Users\nicho\AppData\Local\Programs\Python\Python313\python.exe" `
    "$ProjectRoot\backend\database\seed.py" add_new_product_price 2>&1

Add-Content -Path $LogFile -Value $result

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$timestamp] Finished (exit $LASTEXITCODE)"
