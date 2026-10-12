param([string]$InputDoc,[string]$OutputPdf,[string]$PageInfo)
$ErrorActionPreference='Stop'
$taskWord=$null
$taskDoc=$null
try {
    $taskWord=New-Object -ComObject Word.Application
    $taskWord.Visible=$false
    $taskWord.DisplayAlerts=0
    $taskDoc=$taskWord.Documents.Open($InputDoc,$false,$true)
    $taskDoc.Repaginate()
    $taskPages=$taskDoc.ComputeStatistics(2)
    $taskDoc.ExportAsFixedFormat($OutputPdf,17)
    @{
        pages=$taskPages
        source=$InputDoc
        renderer='Microsoft Word'
    } | ConvertTo-Json | Set-Content -LiteralPath $PageInfo -Encoding utf8
    Write-Output ('PAGES=' + $taskPages)
    $taskDoc.Close(0)
    $taskDoc=$null
} finally {
    if ($taskDoc) { $taskDoc.Close(0) }
    if ($taskWord) { $taskWord.Quit(); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskWord) }
}
