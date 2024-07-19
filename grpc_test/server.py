from concurrent import futures
import grpc
import usage_pb2
import usage_pb2_grpc

class UsageService(usage_pb2_grpc.UsageServiceServicer):
    def GetUsage(self, request, context):
        # ここではサンプルとして固定値を返します
        data_usage = 123456789
        return usage_pb2.UsageResponse(data_usage=data_usage)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    usage_pb2_grpc.add_UsageServiceServicer_to_server(UsageService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()