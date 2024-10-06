import paramiko
import time

# SSH接続情報
hostname = '192.168.3.21'
port = 22
username = 'yoshi'
password = 'yoshi'

# Dockerコンテナ情報
docker_image = 'busybox'
docker_command = 'sh'

# SSH接続の確立
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

# Dockerコンテナの起動
stdin, stdout, stderr = client.exec_command(f'docker run -dit {docker_image} {docker_command}')
container_id = stdout.read().decode().strip()

# コンテナ内での操作
stdin, stdout, stderr = client.exec_command(f'docker exec {container_id} {docker_command}')
print("stdout:",stdout.read().decode())
print("error:",stderr.read().decode())
time.sleep(1)  # 少し待ってから操作を開始

# 例: コンテナ内でのコマンド実行
commands = [
    'echo "Hello from inside the container!"',
    'ls -la',
    'exit'
]

for command in commands:
    stdin, stdout, stderr = client.exec_command(f'docker exec {container_id} {command}')
    print("stdout:",stdout.read().decode())
    print("error:",stderr.read().decode())

# SSH接続の終了
client.close()