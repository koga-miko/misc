cmake_minimum_required(VERSION 3.15)
project(grpc_demo CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Protobuf installation
find_package(Protobuf CONFIG REQUIRED)
message(STATUS "Using protobuf ${Protobuf_VERSION}")

# Find gRPC installation
find_package(gRPC CONFIG REQUIRED)
message(STATUS "Using gRPC ${gRPC_VERSION}")

# Proto file
set(PROTO_FILES
    demo.proto
)

# Generated sources
add_library(grpc_demo_proto ${PROTO_FILES})
target_link_libraries(grpc_demo_proto
    PUBLIC
        protobuf::libprotobuf
        gRPC::grpc
        gRPC::grpc++
)
target_include_directories(grpc_demo_proto PUBLIC ${CMAKE_CURRENT_BINARY_DIR})

# Compile protobuf and grpc files
get_target_property(grpc_cpp_plugin_location gRPC::grpc_cpp_plugin LOCATION)
protobuf_generate(TARGET grpc_demo_proto LANGUAGE cpp)
protobuf_generate(TARGET grpc_demo_proto LANGUAGE grpc GENERATE_EXTENSIONS .grpc.pb.h .grpc.pb.cc PLUGIN "protoc-gen-grpc=${grpc_cpp_plugin_location}")

# Server executable
add_executable(server server.cpp)
target_link_libraries(server
    grpc_demo_proto
    protobuf::libprotobuf
    gRPC::grpc++
)

# Client executable
add_executable(client client.cpp)
target_link_libraries(client
    grpc_demo_proto
    protobuf::libprotobuf
    gRPC::grpc++
)
