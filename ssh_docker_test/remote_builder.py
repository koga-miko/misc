# RemoteBuilderGUIを実行するためのクラスです。
# RemoteBuilderGUIは、リモートサーバー上でビルドを実行するためのGUIです。

import paramiko
import time
import yaml

class RemoteBuilder:
    def __init__(self, build_config_yaml):
        self.set_build_config

    def exec_build(self, build_script_yaml, exec_result_listener):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.build_config['ssh_info']['ip'], self.build_config['ssh_info']['port'], self.build_config['ssh_info']['username'], self.build_config['ssh_info']['password'])

    def cancel_build(self, cancel_result_listener):
        pass

    def set_build_config(self, build_config_yaml):
        with open(build_config_yaml, 'r') as file:
            self.build_config = yaml.safe_load(file)

    def close(self):
        self.ssh.close()

def _send_commands_and_wait_until_done(self, commands, done_reply_message, recv_size_max=1024, timeout=10, sleep_time=1):
    channel = self.ssh.invoke_shell()
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

if __name__ == '__main__':
    # テスト用
    rda = RemoteBuilder()
