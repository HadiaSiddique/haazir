# Haazir deploy: package + deploy the SAM template with the AWS CLI, seed (first time), upload the site.
# Usage:  .\deploy.ps1 [-Seed] [-SiteOnly] [-ModelId <id>]
param([switch]$Seed, [switch]$SiteOnly, [string]$ModelId = "")
$ErrorActionPreference = "Stop"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
$Region = "us-east-1"; $Stack = "haazir"
Set-Location $PSScriptRoot
$Account = (aws sts get-caller-identity --query Account --output text --region $Region)
$Artifacts = "haazir-artifacts-$Account"

if (-not $SiteOnly) {
  aws s3api head-bucket --bucket $Artifacts --region $Region 2>$null
  if ($LASTEXITCODE -ne 0) { aws s3 mb "s3://$Artifacts" --region $Region | Out-Null }
  aws cloudformation package --template-file template.yaml --s3-bucket $Artifacts --output-template-file .packaged.yaml --region $Region | Out-Null
  $overrides = @()
  if ($ModelId) { $overrides = @("--parameter-overrides", "ModelId=$ModelId") }
  aws cloudformation deploy --template-file .packaged.yaml --stack-name $Stack --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --region $Region --no-fail-on-empty-changeset @overrides
  if ($LASTEXITCODE -ne 0) { throw "CloudFormation deploy failed" }
}

$out = aws cloudformation describe-stacks --stack-name $Stack --region $Region --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
$o = @{}; foreach ($x in $out) { $o[$x.OutputKey] = $x.OutputValue }

if ($Seed) {
  aws lambda invoke --function-name haazir-api --payload '{\"action\":\"seed\"}' --cli-binary-format raw-in-base64-out --region $Region .seed-out.json | Out-Null
  Get-Content .seed-out.json
}

"window.HAAZIR_API = '$($o.ApiUrl)';" | Out-File -Encoding ascii frontend\config.js
aws s3 sync frontend "s3://$($o.SiteBucketName)" --delete --region $Region --cache-control "no-cache" | Out-Null
aws cloudfront create-invalidation --distribution-id $o.DistributionId --paths "/*" --region $Region | Out-Null
Write-Host "API : $($o.ApiUrl)"
Write-Host "LIVE: $($o.SiteUrl)"
