# Agenda o robô no Agendador de Tarefas do Windows: 04:17 e 14:17 todos os dias.
# Se o PC estiver desligado no horário, roda assim que ligar. Para remover:
#   Unregister-ScheduledTask -TaskName "Radar Embu - atualizar" -Confirm:$false
$script = Join-Path $PSScriptRoot "atualizar.ps1"
$acao = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$gatilhos = @(
    New-ScheduledTaskTrigger -Daily -At "04:17"
    New-ScheduledTaskTrigger -Daily -At "14:17"
)
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "Radar Embu - atualizar" -Action $acao -Trigger $gatilhos `
    -Settings $config -Description "Coleta dados da Câmara de Embu das Artes e publica o Radar Embu" -Force
