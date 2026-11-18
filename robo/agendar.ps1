# Agenda o robô no Agendador de Tarefas do Windows: 12:00 e 18:00 todos os dias.
# PC desligado no horário: roda assim que ligar. Falhou (sem internet, Câmara fora do ar):
# tenta de novo a cada 30 minutos, até 10 vezes. Para remover:
#   Unregister-ScheduledTask -TaskName "Radar Embu - atualizar" -Confirm:$false
$script = Join-Path $PSScriptRoot "atualizar.ps1"
$acao = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$gatilhos = @(
    New-ScheduledTaskTrigger -Daily -At "12:00"
    New-ScheduledTaskTrigger -Daily -At "18:00"
)
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew `
    -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "Radar Embu - atualizar" -Action $acao -Trigger $gatilhos `
    -Settings $config -Description "Coleta dados da Câmara de Embu das Artes e publica o Radar Embu" -Force
