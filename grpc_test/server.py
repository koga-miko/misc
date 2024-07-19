from concurrent import futures
import grpc
import usage_pb2
import usage_pb2_grpc

class UsageService(usage_pb2_grpc.UsageServiceServicer):
    def GetUsage(self, request, context):
        # ここではサンプルとして固定値を返します
        data_usage = 123456789

        # サーバー側から応答可能な様々なエラー応答の分岐を作成する
        if data_usage < 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Usage is invalid')
            return usage_pb2.UsageResponse()
        elif data_usage > 100000000:
            context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
            context.set_details('Usage is too large')
            return usage_pb2.UsageResponse()
        elif data_usage == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Usage is not found')
            return usage_pb2.UsageResponse()
        elif data_usage == 123456789:
            context.set_code(grpc.StatusCode.OK)
            context.set_details('Usage is found')
            return usage_pb2.UsageResponse(data_usage=data_usage)
        else:
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details('Unknown error')
            return usage_pb2.UsageResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    usage_pb2_grpc.add_UsageServiceServicer_to_server(UsageService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()