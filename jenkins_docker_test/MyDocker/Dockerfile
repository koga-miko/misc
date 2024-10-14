# ubuntu をベースにする
FROM ubuntu:latest

# 環境変数にプロキシ設定を追加  
ENV USER=yoshi
ENV PASS=yoshi_pass

# ワーキングディレクトリを設定
WORKDIR /workspace

# ワーキングディレクトリに必要ファイルをコピー(コピー元は絶対パスは見えないので注意)
COPY set_config.sh /workspace/
COPY data /workspace/

# set_config.shを実行（スクリプト内では上記で設定した環境変数も使用可能）、gitをインストール
RUN chmod +x /workspace/set_config.sh && /workspace/set_config.sh \
    && apt-get update && apt-get install -y git \
    && git config --global user.name "yoshi" \
    && git config --global user.email "yoshi@mail.com"

# コンテナ起動時にBashを実行
CMD ["/bin/bash"]
