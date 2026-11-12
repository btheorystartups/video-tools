param([Parameter(Mandatory=$true)][string]$OutputRoot)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$narrationText = [IO.File]::ReadAllText((Join-Path $OutputRoot 'narration.txt')).Replace("`r`n", "`n")
$narrationSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$eventName = 'VideoInsightRoughCutWordBoundary'
try {
    $narrationSynth.SelectVoice('Microsoft David Desktop')
    $narrationSynth.Rate = -1
    $speechFormat = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
    $narrationSynth.SetOutputToWaveFile((Join-Path $OutputRoot 'narration.wav'), $speechFormat)
    $null = Register-ObjectEvent -InputObject $narrationSynth -EventName SpeakProgress -SourceIdentifier $eventName
    $narrationSynth.Speak($narrationText)
    $wordEvents = @(Get-Event -SourceIdentifier $eventName | ForEach-Object {
        $word = $_.SourceEventArgs
        [PSCustomObject]@{position=$word.CharacterPosition; count=$word.CharacterCount; seconds=$word.AudioPosition.TotalSeconds; text=$word.Text}
    })
    $report = [PSCustomObject]@{voice='Microsoft David Desktop'; rate=-1; kind='local scratch narration, not Brian voice'; words=$wordEvents}
    [IO.File]::WriteAllText((Join-Path $OutputRoot 'speech-timing.json'), ($report | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
    Write-Output ('Captured ' + $wordEvents.Count + ' word timing events')
} finally {
    Unregister-Event -SourceIdentifier $eventName -ErrorAction SilentlyContinue
    Get-Event -SourceIdentifier $eventName -ErrorAction SilentlyContinue | Remove-Event -ErrorAction SilentlyContinue
    $narrationSynth.Dispose()
}
