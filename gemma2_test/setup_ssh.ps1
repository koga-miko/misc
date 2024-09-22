# 管理者権限で実行されているか確認
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole("Administrators")) {
    Start-Process powershell.exe "-File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# WSL 2 インスタンスの IP アドレスを取得
$wslIp = "172.31.63.58"

# 通信を許可するポート番号
$ports = @(22)

# 以前に作成されたファイアウォールの例外ルールを削除
Remove-NetFireWallRule -DisplayName 'WSL 2 Firewall Unlock'

# ファイアウォールの例外ルールを作成
foreach ($port in $ports) {
    New-NetFireWallRule -DisplayName 'WSL 2 Firewall Unlock' -Direction Outbound -LocalPort $port -Action Allow -Protocol TCP
    New-NetFireWallRule -DisplayName 'WSL 2 Firewall Unlock' -Direction Inbound -LocalPort $port -Action Allow -Protocol TCP
}

# ポートフォワーディングの設定
foreach ($port in $ports) {
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=* connectport=$port connectaddress=$wslIp
}

# 設定の確認
netsh interface portproxy show v4tov4
