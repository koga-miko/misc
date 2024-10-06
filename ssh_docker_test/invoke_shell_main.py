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

def send_commands_and_wait_until_done(commands, done_reply_message, recv_size_max=1024, timeout=10, sleep_time=1):
    channel = ssh.invoke_shell()
    for command in commands:
        # インタラクティブなシェルセッションを開始
        print(f"Sending command: {command}")
        channel.send(command + '\n')
    time.sleep(sleep_time)
    start_time = time.time()
    while True:
        if channel.recv_ready():
            output = channel.recv(recv_size_max).decode('utf-8')
            print(f"Received output: {output}", end='')
            if done_reply_message in output:
                print(f"Received done message: {done_reply_message}. Exiting.")
                break
        if time.time() - start_time > timeout:
            print(f"Timeout reached. Exiting.")
            break
        time.sleep(sleep_time)
    channel.close()

send_commands_and_wait_until_done(["docker run -dit --name busybox_container busybox sh","docker attach busybox_container", "ls -la"], "drwx")

# SSH接続の終了
ssh.close()
