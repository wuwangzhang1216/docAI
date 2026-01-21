# Delete all GitHub Actions workflow runs
$repo = "wuwangzhang1216/docAI"

# Get all run IDs and delete them
gh run list --repo $repo --limit 200 --json databaseId --jq ".[].databaseId" | ForEach-Object {
    Write-Host "Deleting run $_"
    gh run delete $_ --repo $repo
}

Write-Host "Done!"
