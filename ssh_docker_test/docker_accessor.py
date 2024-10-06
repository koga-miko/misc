# このクラスの機能
# リモートのDockerコンテナを使ってコマンドを実行する


import paramiko
import time

class RemoteDockerAccessor:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, hostname, port, username, password):
        self.ssh.connect(hostname, port, username, password)

        self.container_id = None
