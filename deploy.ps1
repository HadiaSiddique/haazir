# Haazir deploy: package + deploy the SAM template with the AWS CLI, seed (first time), publish the site.
# Usage:  .\deploy.ps1 [-Seed] [-Cdn] [-ModelId <id>]
#   The site is always served by the API Lambda (same URL as the API). -Cdn also creates S3 + CloudFront.
param([switch]$Seed, [switch]$Cdn, [string]$ModelId = "")
$ErrorActionPreference = "Continue"  # native CLI stderr must not abort; we check $LASTEXITCODE
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
$Region = "us-east-1"; $Stack = "haazir"
Set-Location $PSScriptRoot
$Account = (aws sts get-caller-identity --query Account --output text --region $Region)
$Artifacts = "haazir-artifacts-$Account"

# bundle the static site into the Lambda package
Remove-Item -Recurse -Force backend\static -ErrorAction SilentlyContinue
New-Item -ItemType Directory backend\static | Out-Null
Copy-Item frontend\index.html, frontend\app.js, frontend\styles.css backend\static\
if (Test-Path frontend\og.png) { Copy-Item frontend\og.png backend\static\ }
Get-ChildItem -Recurse -Directory -Filter __pycache__ backend | Remove-Item -Recurse -Force

aws s3api head-bucket --bucket $Artifacts --region $Region 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { aws s3 mb "s3://$Artifacts" --region $Region | Out-Null }
aws cloudformation package --template-file template.yaml --s3-bucket $Artifacts --output-template-file .packaged.yaml --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) { throw "package failed" }
$params = @("EnableCdn=$(if ($Cdn) { 'true' } else { 'false' })")
if ($ModelId) { $params += "ModelId=$ModelId" }
aws cloudformation deploy --template-file .packaged.yaml --stack-name $Stack --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --region $Region --no-fail-on-empty-changeset --parameter-overrides @params
if ($LASTEXITCODE -ne 0) { throw "CloudFormation deploy failed" }

$out = aws cloudformation describe-stacks --stack-name $Stack --region $Region --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
$o = @{}; foreach ($x in $out) { $o[$x.OutputKey] = $x.OutputValue }

if ($Seed) {
  aws lambda invoke --function-name haazir-api --payload '{\"action\":\"seed\"}' --cli-binary-format raw-in-base64-out --region $Region .seed-out.json | Out-Null
  Get-Content .seed-out.json
}

if ($o.SiteBucketName) {
  "window.HAAZIR_API = '$($o.ApiUrl)';" | Out-File -Encoding ascii frontend\config.js
  aws s3 sync frontend "s3://$($o.SiteBucketName)" --delete --region $Region --cache-control "no-cache" | Out-Null
  aws cloudfront create-invalidation --distribution-id $o.DistributionId --paths "/*" | Out-Null
  Write-Host "CDN : $($o.SiteUrl)"
}
Write-Host "LIVE: $($o.ApiUrl)/"
