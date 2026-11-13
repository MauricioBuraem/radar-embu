# Robô do Radar Embu: coleta os dados da Câmara, gera o site e envia ao GitHub
# (o envio dispara a publicação no GitHub Pages). Agendado pelo robo/agendar.ps1.
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
$env:PYTHONIOENCODING = "utf-8"
$log = Join-Path $raiz "dados\cache\robo.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null

function Registrar($msg) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg" | Out-File $log -Append -Encoding utf8 }
function Rodar($exe, [string[]]$args_) {
    $ErrorActionPreference = "Continue"   # git escreve progresso no stderr
    $saida = & $exe @args_ 2>&1 | Out-String
    $saida | Out-File $log -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw "$exe $($args_ -join ' ') saiu com código $LASTEXITCODE" }
}

$py = Join-Path $raiz ".venv\Scripts\python.exe"
try {
    Registrar "início"
    Rodar git @("pull", "--rebase", "--autostash", "-q")
    Rodar $py @("-m", "coletor")
    Rodar $py @("-m", "coletor.site")
    Rodar git @("add", "dados/embu.json", "site/dados.js", "site/fotos")
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        Rodar git @("commit", "-q", "-m", "dados: atualização automática $(Get-Date -Format 'yyyy-MM-dd HH:mm')")
        Rodar git @("push", "-q")
        Registrar "dados novos enviados"
    } else {
        Registrar "nada mudou"
    }
} catch {
    Registrar "ERRO: $_"
    exit 1
}
