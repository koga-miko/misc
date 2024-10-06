import paramiko
import threading
import time

# リモートPCへの接続情報
remote_host = '192.168.3.21'
remote_port = 22
remote_user = 'yoshi'
remote_password = 'yoshi'

# SSHクライアントのセットアップ
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(remote_host, port=remote_port, username=remote_user, password=remote_password)

channel = ssh.invoke_shell()

def send_commands_and_wait_until_done(command, done_reply_message, recv_size_max=1024, timeout=10, sleep_time=1):
    # インタラクティブなシェルセッションを開始
    channel.send(command + '\n')
    time.sleep(sleep_time)
    start_time = time.time()
    while True:
        if channel.recv_ready():
            output = channel.recv(recv_size_max).decode('utf-8')
            print(f"Received output: {output}", end='')
            if done_reply_message in output:
                break
        if time.time() - start_time > timeout:
            print(f"Timeout reached. Exiting.")
            break
        time.sleep(sleep_time)

# コマンドを送信する関数
def send_commands():
    time.sleep(10)
    commands = ['docker exec -it 00a59344b771 sh']
    for command in commands:
        print(f"Sending command: {command}")
        channel.send(command + '\n')
        time.sleep(1)  # コマンドの実行を待つ
    # コマンド入力を受け付ける
    while True:
        command = input()
        if channel.send_ready():
            channel.send(command + '\n')
        else:
            print("Channel is not ready to send data.")
            exit()
        time.sleep(1)

# 出力を受信する関数
def receive_output():
    while True:
        if channel.recv_ready():
            output = channel.recv(1024).decode('utf-8')
            print(f"Received output: {output}", end='')
        time.sleep(1)

# スレッドの作成
send_thread = threading.Thread(target=send_commands)
recv_thread = threading.Thread(target=receive_output)

# スレッドの開始
send_thread.start()
recv_thread.start()

# スレッドの終了を待つ
send_thread.join()
recv_thread.join()

# SSH接続の終了
ssh.close()
