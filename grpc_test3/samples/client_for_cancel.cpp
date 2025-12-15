// client.cpp
#include <grpcpp/grpcpp.h>
#include <atomic>
#include <thread>
#include "example.grpc.pb.h"

using grpc::ClientContext;
using grpc::ClientReaderWriter;
using grpc::Status;

class ExampleClient {
public:
  void BidirectionalStreamingCall() {
    ClientContext context;
    std::unique_ptr<ClientReaderWriter<Request, Response>> stream(
        stub_->BidirectionalStreamingCall(&context));

    std::atomic<bool> stop_sending{false};
    std::atomic<bool> stop_receiving{false};
    std::atomic<bool> user_cancelled{false};

    // 送信スレッド
    std::thread writer([&]() {
      int count = 0;
      while (!stop_sending && !user_cancelled) {
        Request request;
        request.set_message("Message " + std::to_string(count++));
        request.set_id(count);
        
        if (!stream->Write(request)) {
          std::cout << "Write failed (server closed)" << std::endl;
          break;
        }
        
        std::this_thread::sleep_for(std::chrono::seconds(1));
        
        // 例：10個送ったら送信停止
        if (count >= 10) {
          std::cout << "Client: Stopping send..." << std::endl;
          stop_sending = true;
        }
      }
      
      // 送信を終了することをサーバーに通知
      // これを呼ぶとサーバー側のRead()がfalseを返す
      stream->WritesDone();
      std::cout << "Client: WritesDone called" << std::endl;
    });

    // 受信スレッド
    std::thread reader([&]() {
      Response response;
      int recv_count = 0;
      
      while (!stop_receiving && !user_cancelled) {
        if (stream->Read(&response)) {
          std::cout << "Received: " << response.result() << std::endl;
          recv_count++;
          
          // 例：5個受信したら受信停止
          if (recv_count >= 5) {
            std::cout << "Client: Stopping receive..." << std::endl;
            stop_receiving = true;
          }
        } else {
          // サーバーが送信を終了した
          std::cout << "Server finished sending" << std::endl;
          break;
        }
      }
      std::cout << "Client: Receiver thread finished" << std::endl;
    });

    // メインスレッドでユーザー入力待ち（例）
    std::cout << "Press 'q' to quit, 's' to stop sending, 'r' to stop receiving" << std::endl;
    char c;
    while (std::cin >> c) {
      if (c == 'q') {
        user_cancelled = true;
        context.TryCancel();  // RPCをキャンセル
        break;
      } else if (c == 's') {
        stop_sending = true;
        std::cout << "User requested: stop sending" << std::endl;
      } else if (c == 'r') {
        stop_receiving = true;
        std::cout << "User requested: stop receiving" << std::endl;
      }
    }

    writer.join();
    reader.join();
    
    Status status = stream->Finish();
    std::cout << "RPC Status: " << (status.ok() ? "OK" : status.error_message()) << std::endl;
  }

private:
  std::unique_ptr<ExampleService::Stub> stub_;
};
