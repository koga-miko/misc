#!/bin/bash
# セットアップスクリプト - 依存関係のインストールとprotoファイルのコンパイル

set -e

echo "========================================="
echo "gRPC Demo Setup"
echo "========================================="

# 依存関係のインストール
echo ""
echo "[1/2] Installing dependencies..."
pip3 install -r requirements.txt

# protoファイルからPythonコードを生成
echo ""
echo "[2/2] Generating Python code from proto file..."
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. demo.proto

echo ""
echo "========================================="
echo "✓ Setup completed successfully!"
echo "========================================="
echo ""
echo "To run the demo:"
echo "  1. Start server: python3 server.py"
echo "  2. Start client: python3 client.py"
echo ""
