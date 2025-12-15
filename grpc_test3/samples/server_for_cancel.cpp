// server.cpp
#include <grpcpp/grpcpp.h>
#include <atomic>
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>

using grpc::ServerContext;
using grpc::ServerReaderWriter;
using grpc::Status;

class ExampleServiceImpl final : public ExampleService::Service {
public:
  Status BidirectionalStreamingCall(ServerContext* context,
                                   ServerReaderWriter<Response, Request>* stream) override {
    std::atomic<bool> stop_sending{false};
    std::atomic<bool> stop_receiving{false};
    std::queue<Response> send_queue;
    std::mutex queue_mutex;
    std::condition_variable queue_cv;

    // 受信スレッド
    std::thread reader([&]() {
      Request request;
      int recv_count = 0;
      
      while (!stop_receiving && !context->IsCancelled()) {
        if (stream->Read(&request)) {
          std::cout << "Server received: " << request.message() << std::endl;
          recv_count++;
          
          // 条件によって受信停止を決定
          if (recv_count >= 10) {
            std::cout << "Server: Reached max receives, stopping..." << std::endl;
            stop_receiving = true;
            break;
          }
          
          // 受信したメッセージに基づいてレスポンスを生成
          Response response;
          response.set_result("Echo: " + request.message());
          response.set_code(request.id());
          
          {
            std::lock_guard<std::mutex> lock(queue_mutex);
            send_queue.push(response);
          }
          queue_cv.notify_one();
          
        } else {
          // クライアントがWritesDone()を呼んだ
          std::cout << "Server: Client finished sending" << std::endl;
          break;
        }
      }
      
      std::cout << "Server: Reader thread finished" << std::endl;
      // 受信終了を送信スレッドに通知
      stop_sending = true;
      queue_cv.notify_one();
    });

    // 送信スレッド
    std::thread writer([&]() {
      int send_count = 0;
      
      while (!stop_sending && !context->IsCancelled()) {
        std::unique_lock<std::mutex> lock(queue_mutex);
        
        // メッセージが来るまで、または停止シグナルまで待機
        queue_cv.wait_for(lock, std::chrono::seconds(1), [&]() {
          return !send_queue.empty() || stop_sending || context->IsCancelled();
        });
        
        if (stop_sending || context->IsCancelled()) {
          break;
        }
        
        while (!send_queue.empty()) {
          Response response = send_queue.front();
          send_queue.pop();
          lock.unlock();
          
          if (!stream->Write(response)) {
            std::cout << "Server: Write failed (client disconnected)" << std::endl;
            stop_sending = true;
            break;
          }
          
          send_count++;
          
          // 条件によって送信停止を決定
          if (send_count >= 15) {
            std::cout << "Server: Reached max sends, stopping..." << std::endl;
            stop_sending = true;
            break;
          }
          
          lock.lock();
        }
      }
      
      std::cout << "Server: Writer thread finished" << std::endl;
    });

    reader.join();
    writer.join();
    
    if (context->IsCancelled()) {
      return Status::CANCELLED;
    }
    
    return Status::OK;
  }
};
