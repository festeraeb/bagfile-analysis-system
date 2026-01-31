$patterns = 'sonar','SONARSNIFFER','sonarsniffer','Garmin','cesarops','CESAROPS'
$forbidden = 'magnetic','\bbag\b','swayze','s102','pm18','ai4shipwrecks','newspaper','scrap','HistoryofCESARSNIFFERBAGFILE','Lake Erie Bag Files'
$root = Get-Location
$files = Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    $rel = $_.FullName.Substring($root.Path.Length+1)
    $match = $false
    foreach ($pat in $patterns) { if ($rel -match $pat) { $match = $true; break } }
    if (-not $match) { return $false }
    foreach ($f in $forbidden) { if ($rel -match $f) { return $false } }
    if ($rel -match '^sonar_sniffer_master\\' -or $rel -match '^cesarops_master\\') { return $false }
    return $true
}
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$post = "MOVE_MANIFEST_POST_$ts.md"
"# Post-move manifest - $ts`n`n" | Out-File -FilePath $post -Encoding utf8
"## Moved files:`n" | Out-File -FilePath $post -Append
foreach ($f in $files) {
    $rel = $f.FullName.Substring($root.Path.Length+1)
    $dest = $null
    if ($rel -match 'sonar|SONARSNIFFER|sonarsniffer|Garmin') { $dest = Join-Path $root 'sonar_sniffer_master' }
    elseif ($rel -match 'cesarops|CESAROPS') { $dest = Join-Path $root 'cesarops_master' }
    if ($dest) {
        # ensure directory structure
        $destDir = Join-Path $dest (Split-Path $rel -Parent)
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        $target = Join-Path $dest $rel
        Move-Item -LiteralPath $f.FullName -Destination $target -Force
        "$rel -> $( (Resolve-Path $target).Path )" | Out-File -FilePath $post -Append
    }
}
"`n## Git status snapshot:`n" | Out-File -FilePath $post -Append
# capture git status if available
try { git status --porcelain | Out-File -FilePath $post -Append } catch { "(git not available)" | Out-File -FilePath $post -Append }
Write-Output "Auto-move complete. Post-manifest: $post"
