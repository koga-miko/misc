# client_server_test.py
import socket
import threading
import time
from packet_holder import PacketHolder

aborted = False
def server(server_address):
    global aborted
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(1)
    server_socket.settimeout(3)
    while True:
        try:
            server_for_responce_socket = None
            server_for_responce_socket, _ = server_socket.accept()
        except socket.timeout as e:
            if aborted:
                break
            else:
                continue
        while True:
            data = server_for_responce_socket.recv(1024)
            if not data or aborted:
                break
            server_for_responce_socket.sendall(b"Received:"+data)
    if server_for_responce_socket:
        server_for_responce_socket.close()
    server_socket.close()

if __name__ == "__main__":
    REAL_SERVER_ADDRESS = ('localhost', 6000)
    PACKET_HOLDER_ADDRESS = ('localhost', 16000)

    server_thread = threading.Thread(target=server, args=(REAL_SERVER_ADDRESS,))
    server_thread.start()

    time.sleep(1)  # Ensure server is running before client

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while aborted is False:
        try:
            client_socket.connect(PACKET_HOLDER_ADDRESS)
            for _ in range(100):
                for i in range(111, 500, 111):
                    client_socket.sendall(str(i).encode())
                    time.sleep(1)
        except KeyboardInterrupt:
            break
        except ConnectionRefusedError as e:
            try:
                time.sleep(5)
            except KeyboardInterrupt:
                break
            else:
                print(f"Connection refused to {PACKET_HOLDER_ADDRESS}: retrying ...")
                continue
        except Exception as e:
            print(f"An error occurred while connecting to {PACKET_HOLDER_ADDRESS}: {str(e)}")
            break
    aborted = True
    client_socket.close()
    server_thread.join()
