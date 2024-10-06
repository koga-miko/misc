# Dockerコンテナを使ってビルドを実行して出来上がったファイルを取得するためのクラスを作成します。
# DockerコンテナへのアクセスはSSHを経由しておこないます。
# 以下のクラスを完成させてください。

import paramiko
import time

class RemoteDockerAccessor:
    def __init__(self):
        pass

    def exec_build(self, build_script_yaml, exec_result_listener):
        pass

    def cancel_build(self, cancel_result_listener):
        pass

    def set_config(self, config_yaml):
        pass

    def close(self):
        self.ssh.close()

if __name__ == '__main__':
    # テスト用
    rda = RemoteDockerAccessor()
