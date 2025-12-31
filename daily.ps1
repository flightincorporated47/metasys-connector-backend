# daily.ps1 - CSUDH Pilot daily routine (git + export SOPs)
$ErrorActionPreference = "Stop"

Write-Host "== CSUDH Pilot Daily Routine =="

# 1) Show repo status
Write-Host "`n[1/5] Git status"
git status

# 2) Stage SOPs + tools
Write-Host "`n[2/5] Staging SOPs + tools"
git add docs/SOPs
git add tools

# 3) Commit if needed
Write-Host "`n[3/5] Commit (only if there are staged changes)"
$staged = git diff --cached --name-only
if ($staged) {
  git commit -m "Daily SOP/tool update (CSUDH pilot)"
  git push
} else {
  Write-Host "No staged changes. Skipping commit/push."
}

# 4) Export SOPs locally
Write-Host "`n[4/5] Exporting SOPs to DOCX/PDF (local)"
python .\tools\export_sops.py --root . --out .\exports --combine

# 5) Open combined exports folder
Write-Host "`n[5/5] Opening exports folder"
explorer .\exports\combined

Write-Host "`nDone."

