#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <chrono>

#include <grpcpp/grpcpp.h>
#include "demo.grpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::ServerReader;
using grpc::ServerWriter;
using grpc::ServerReaderWriter;
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

class DemoServiceImpl final : public DemoService::Service {
public:
    // 1. Unary RPC: 単純なリクエスト-レスポンス
    Status UnaryCall(ServerContext* context, const SimpleRequest* request,
                     SimpleResponse* response) override {
        std::cout << "[Unary] Received: " << request->name() << std::endl;
        response->set_message("Hello, " + request->name() + "!");
        return Status::OK;
    }

    // 2. Server Streaming RPC: サーバーからのストリーミング
    Status ServerStreamingCall(ServerContext* context, const StreamRequest* request,
                               ServerWriter<StreamResponse>* writer) override {
        std::cout << "[Server Streaming] Count: " << request->count() << std::endl;

        for (int i = 0; i < request->count(); ++i) {
            StreamResponse response;
            response.set_index(i);
            response.set_message("Message #" + std::to_string(i));

            std::cout << "[Server Streaming] Sending: " << response.message() << std::endl;
            writer->Write(response);

            // 少し待機してストリーミングを可視化
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }

        return Status::OK;
    }

    // 3. Client Streaming RPC: クライアントからのストリーミング
    Status ClientStreamingCall(ServerContext* context,
                               ServerReader<ClientStreamRequest>* reader,
                               ClientStreamResponse* response) override {
        std::cout << "[Client Streaming] Waiting for client messages..." << std::endl;

        ClientStreamRequest request;
        int count = 0;
        std::string accumulated_data;

        while (reader->Read(&request)) {
            std::cout << "[Client Streaming] Received: " << request.data() << std::endl;
            accumulated_data += request.data() + " ";
            count++;
        }

        response->set_result("Received " + std::to_string(count) + " messages: " + accumulated_data);
        response->set_count(count);

        return Status::OK;
    }

    // 4. Bidirectional Streaming RPC: 双方向ストリーミング
    Status BidirectionalStreamingCall(ServerContext* context,
                                      ServerReaderWriter<BidiResponse, BidiRequest>* stream) override {
        std::cout << "[Bidirectional Streaming] Started" << std::endl;

        BidiRequest request;
        int message_count = 0;

        while (stream->Read(&request)) {
            std::cout << "[Bidirectional Streaming] Received: " << request.message() << std::endl;

            BidiResponse response;
            response.set_reply("Echo #" + std::to_string(message_count) + ": " + request.message());

            std::cout << "[Bidirectional Streaming] Sending: " << response.reply() << std::endl;
            stream->Write(response);

            message_count++;
        }

        std::cout << "[Bidirectional Streaming] Completed. Total messages: " << message_count << std::endl;
        return Status::OK;
    }
};

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    DemoServiceImpl service;

    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);

    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;
    std::cout << "===========================================\n";
    std::cout << "Available RPC methods:\n";
    std::cout << "1. UnaryCall\n";
    std::cout << "2. ServerStreamingCall\n";
    std::cout << "3. ClientStreamingCall\n";
    std::cout << "4. BidirectionalStreamingCall\n";
    std::cout << "===========================================\n";

    server->Wait();
}

int main(int argc, char** argv) {
    RunServer();
    return 0;
}
