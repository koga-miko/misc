# gRPC C++ Demo - 4つの通信方法

このプロジェクトは、gRPCの4つの通信方法をC++で実装したデモです。

## 4つの通信方法

1. **Unary RPC** - 単純なリクエスト-レスポンス
2. **Server Streaming RPC** - サーバーからのストリーミング
3. **Client Streaming RPC** - クライアントからのストリーミング
4. **Bidirectional Streaming RPC** - 双方向ストリーミング

## ファイル構成

```
.
├── demo.proto          # プロトコル定義ファイル
├── server.cpp          # サーバー実装
├── client.cpp          # クライアント実装
├── CMakeLists.txt      # ビルド設定
└── README.md           # このファイル
```

## 必要な環境

- CMake 3.15以上
- C++17対応のコンパイラ
- gRPC
- Protocol Buffers

### macOSでの依存関係インストール

```bash
# Homebrewを使用
brew install grpc protobuf cmake
```

### Ubuntuでの依存関係インストール

```bash
sudo apt-get update
sudo apt-get install -y cmake build-essential autoconf libtool pkg-config
sudo apt-get install -y libgrpc++-dev libprotobuf-dev protobuf-compiler-grpc
```

## ビルド方法

```bash
# ビルドディレクトリを作成
mkdir build
cd build

# CMakeでビルド設定を生成
cmake ..

# ビルドを実行
cmake --build .
```

## 実行方法

### サーバーの起動

```bash
# buildディレクトリから実行
./server
```

サーバーが起動すると、以下のように表示されます：

```
Server listening on 0.0.0.0:50051
===========================================
Available RPC methods:
1. UnaryCall
2. ServerStreamingCall
3. ClientStreamingCall
4. BidirectionalStreamingCall
===========================================
```

### クライアントの実行

別のターミナルを開いて：

```bash
# buildディレクトリから実行
./client
```

クライアントは自動的に4つの通信方法すべてをテストします。

## 実行例

### サーバー側の出力例

```
Server listening on 0.0.0.0:50051
[Unary] Received: World
[Server Streaming] Count: 5
[Server Streaming] Sending: Message #0
[Server Streaming] Sending: Message #1
...
[Client Streaming] Waiting for client messages...
[Client Streaming] Received: Data_0
[Client Streaming] Received: Data_1
...
[Bidirectional Streaming] Started
[Bidirectional Streaming] Received: Message_0
[Bidirectional Streaming] Sending: Echo #0: Message_0
...
```

### クライアント側の出力例

```
=========================================
gRPC C++ Demo Client
Testing all 4 communication patterns
=========================================

=== Testing Unary RPC ===
Response: Hello, World!

=== Testing Server Streaming RPC ===
Received [0]: Message #0
Received [1]: Message #1
...
Server streaming completed successfully

=== Testing Client Streaming RPC ===
Sending: Data_0
Sending: Data_1
...
Server response: Received 3 messages: Data_0 Data_1 Data_2
Total count: 3

=== Testing Bidirectional Streaming RPC ===
Sending: Message_0
Received: Echo #0: Message_0
...
Bidirectional streaming completed successfully

=========================================
All tests completed!
=========================================
```

## 各通信方法の説明

### 1. Unary RPC
最も基本的な通信方法。クライアントが1つのリクエストを送信し、サーバーが1つのレスポンスを返します。

### 2. Server Streaming RPC
クライアントがリクエストを送信すると、サーバーが複数のレスポンスをストリームで返します。

### 3. Client Streaming RPC
クライアントが複数のリクエストをストリームで送信し、サーバーが1つのレスポンスを返します。

### 4. Bidirectional Streaming RPC
クライアントとサーバーがそれぞれ独立したストリームで送受信を行います。非同期で双方向の通信が可能です。

## トラブルシューティング

### ポート50051が既に使用されている場合

サーバーのポート番号を変更してください：

```cpp
// server.cppの該当行を修正
std::string server_address("0.0.0.0:50052");
```

```cpp
// client.cppの該当行を修正
std::string server_address("localhost:50052");
```

### gRPCが見つからない場合

CMakeにgRPCのインストールパスを指定してください：

```bash
cmake -DCMAKE_PREFIX_PATH=/path/to/grpc ..
```

## ライセンス

このサンプルコードは自由に使用・改変できます。
