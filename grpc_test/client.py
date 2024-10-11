import grpc
import usage_pb2
import usage_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = usage_pb2_grpc.UsageServiceStub(channel)
        response = stub.GetUsage(usage_pb2.UsageRequest(start_time=1609459200, end_time=1612137600))
        print("Data usage:", response.data_usage)

if __name__ == '__main__':
    run()
