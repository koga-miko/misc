#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <chrono>

#include <grpcpp/grpcpp.h>
#include "demo.grpc.pb.h"

using grpc::Channel;
using grpc::ClientContext;
using grpc::ClientReader;
using grpc::ClientWriter;
using grpc::ClientReaderWriter;
using grpc::Status;

using demo::DemoService;
using demo::SimpleRequest;
using demo::SimpleResponse;
using demo::StreamRequest;
using demo::StreamResponse;
using demo::ClientStreamRequest;
using demo::ClientStreamResponse;
using demo::BidiRequest;
using demo::BidiResponse;

class DemoClient {
public:
    DemoClient(std::shared_ptr<Channel> channel)
        : stub_(DemoService::NewStub(channel)) {}

    // 1. Unary RPC
    void TestUnaryCall(const std::string& name) {
        std::cout << "\n=== Testing Unary RPC ===\n";

        SimpleRequest request;
        request.set_name(name);

        SimpleResponse response;
        ClientContext context;

        Status status = stub_->UnaryCall(&context, request, &response);

        if (status.ok()) {
            std::cout << "Response: " << response.message() << std::endl;
        } else {
            std::cout << "RPC failed: " << status.error_message() << std::endl;
        }
    }

    // 2. Server Streaming RPC
    void TestServerStreamingCall(int count) {
        std::cout << "\n=== Testing Server Streaming RPC ===\n";

        StreamRequest request;
        request.set_count(count);

        StreamResponse response;
        ClientContext context;

        std::unique_ptr<ClientReader<StreamResponse>> reader(
            stub_->ServerStreamingCall(&context, request));

        while (reader->Read(&response)) {
            std::cout << "Received [" << response.index() << "]: "
                      << response.message() << std::endl;
        }

        Status status = reader->Finish();
        if (status.ok()) {
            std::cout << "Server streaming completed successfully\n";
        } else {
            std::cout << "RPC failed: " << status.error_message() << std::endl;
        }
    }

    // 3. Client Streaming RPC
    void TestClientStreamingCall(int count) {
        std::cout << "\n=== Testing Client Streaming RPC ===\n";

        ClientStreamResponse response;
        ClientContext context;

        std::unique_ptr<ClientWriter<ClientStreamRequest>> writer(
            stub_->ClientStreamingCall(&context, &response));

        for (int i = 0; i < count; ++i) {
            ClientStreamRequest request;
            request.set_data("Data_" + std::to_string(i));

            std::cout << "Sending: " << request.data() << std::endl;
            writer->Write(request);

            std::this_thread::sleep_for(std::chrono::milliseconds(300));
        }

        writer->WritesDone();
        Status status = writer->Finish();

        if (status.ok()) {
            std::cout << "Server response: " << response.result() << std::endl;
            std::cout << "Total count: " << response.count() << std::endl;
        } else {
            std::cout << "RPC failed: " << status.error_message() << std::endl;
        }
    }

    // 4. Bidirectional Streaming RPC
    void TestBidirectionalStreamingCall(int count) {
        std::cout << "\n=== Testing Bidirectional Streaming RPC ===\n";

        ClientContext context;

        std::shared_ptr<ClientReaderWriter<BidiRequest, BidiResponse>> stream(
            stub_->BidirectionalStreamingCall(&context));

        // 送信スレッド
        std::thread writer([&stream, count]() {
            for (int i = 0; i < count; ++i) {
                BidiRequest request;
                request.set_message("Message_" + std::to_string(i));

                std::cout << "Sending: " << request.message() << std::endl;
                stream->Write(request);

                std::this_thread::sleep_for(std::chrono::milliseconds(500));
            }
            stream->WritesDone();
        });

        // 受信処理
        BidiResponse response;
        while (stream->Read(&response)) {
            std::cout << "Received: " << response.reply() << std::endl;
        }

        writer.join();

        Status status = stream->Finish();
        if (status.ok()) {
            std::cout << "Bidirectional streaming completed successfully\n";
        } else {
            std::cout << "RPC failed: " << status.error_message() << std::endl;
        }
    }

private:
    std::unique_ptr<DemoService::Stub> stub_;
};

int main(int argc, char** argv) {
    std::string server_address("localhost:50051");

    DemoClient client(
        grpc::CreateChannel(server_address, grpc::InsecureChannelCredentials()));

    std::cout << "=========================================\n";
    std::cout << "gRPC C++ Demo Client\n";
    std::cout << "Testing all 4 communication patterns\n";
    std::cout << "=========================================\n";

    // 全ての通信方法をテスト
    client.TestUnaryCall("World");

    std::this_thread::sleep_for(std::chrono::seconds(1));
    client.TestServerStreamingCall(5);

    std::this_thread::sleep_for(std::chrono::seconds(1));
    client.TestClientStreamingCall(3);

    std::this_thread::sleep_for(std::chrono::seconds(1));
    client.TestBidirectionalStreamingCall(4);

    std::cout << "\n=========================================\n";
    std::cout << "All tests completed!\n";
    std::cout << "=========================================\n";

    return 0;
}
