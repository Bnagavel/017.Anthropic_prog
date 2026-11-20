$dir = "C:\Bask\00.AI\017.Anthropic_prog\cv"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open("$dir\cv_source.html")
    $doc.PageSetup.TopMargin = 36; $doc.PageSetup.BottomMargin = 32
    $doc.PageSetup.LeftMargin = 40; $doc.PageSetup.RightMargin = 40
    $doc.PageSetup.PageWidth = 595.3; $doc.PageSetup.PageHeight = 841.9
    $doc.Repaginate()
    "Pages: " + $doc.ComputeStatistics(2)
    $doc.SaveAs2("$dir\Baskaran_Nagavel_AI_Safety_CV.docx", 12)
    $doc.SaveAs2("$dir\Baskaran_Nagavel_AI_Safety_CV.pdf", 17)
    $doc.Close(0)
} finally { $word.Quit() }
Get-ChildItem $dir | Select-Object Name, Length
