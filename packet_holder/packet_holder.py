# packet_holder.py
# Description: This file contains the PacketHolder class, which is used to hold
# packets in a socket channel between a client and a server.
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import datetime
import queue
import re
from threading import Lock
from threading import Thread
import socket
import time

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# PacketHolder
# ------------------------------------------------------------------------------
class PacketHolder:
    PACKET_MAX_SIZE = 65536
    RETRY_COUNT = 100
    RETRY_INTERBAL = 3

    def __init__(self):
        self.packet_hold_status = False
        self.keywords = []
        self.server_sending_lock = Lock()
        self.queue = queue.Queue()
        self.bind_address = None
        self.client_socket = None
        self.client_address = None
        self.server_address = None
        self.server_socket = None
        self.started = False
        self.server_connected = False
        self.c2s_thread = None
        self.s2c_thread = None
        self.starting_thread = None
        self.output_only_pending_packets = False

    def register_pending_keyword(self, keyword):
        if not isinstance(keyword, str):
            raise ValueError("keyword should be a string")
        self.keywords.append(keyword)

    def register_pending_keywords(self, keywords):
        if not isinstance(keywords, list):
            raise ValueError("keywords should be a list")
        self.keywords += keywords

    def clear_pending_keywords(self):
        self.keywords = []

    # Start the packet holder. this method will block until the server is stopped.
    def start(self, packet_holder_ip, packet_holder_port, server_ip, server_port, wait=False):
        if self.started:
            print("Process is already started")
            return
        if self.server_connected:
            print("Server is already connected")
            return
        self.started = True
        self.bind_address = (packet_holder_ip, packet_holder_port)
        self.server_address = (server_ip, server_port)
        if wait:
            try:
                self._start_internal()
                self._wait_for_threads_join()
            except Exception as e:
                print(f"An error occurred while processing the packet holder: {str(e)}")
                self._close_sockets()
                exit(1)
        else:
            self.starting_thread = Thread(target=self._start_internal)
            self.starting_thread.start()

    def stop(self):
        if not self.started:
            print("Process is already stopped")
            return
        print("Stopping the packet holder ...")
        self._close_sockets()
        self._wait_for_threads_join()
        self.started = False
        print("Packet holder is stopped successfully.")
        
    def set_packet_hold_status(self, status):
        if not self.started:
            print("Process is not started")
            return
        self.packet_hold_status = status

    def send_pending_packets(self):
        if not self.started:
            print("Process is not started")
            return
        packet = self._dequeue_packet()
        while packet is not None:
            self._pass_through_client_to_server_delayed(packet)
            packet = self._dequeue_packet()
    
    def set_output_only_pending_packets(self, status):
        if status:
            self.output_only_pending_packets = True
        else:
            self.output_only_pending_packets = False

    def _start_internal(self):
        try:
            print("Creating server for the this packet holder ...")
            self.bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"Binding to {self.bind_address}")
            self.bind_socket.bind(self.bind_address)
            print("Listening ...")
            self.bind_socket.listen(1)
            print("Accepting ...")
            self.client_socket, self.client_address = self.bind_socket.accept()
        except Exception as e:
            print(f"An error occurred while accepting from {self.bind_address}, error: {str(e)}")
            return
        print("Server for packet holder is created successfully.")
        self._connect_to_server()
        self.c2s_thread = Thread(target=self._handle_client_to_server)
        self.c2s_thread.start()
        self.s2c_thread = Thread(target=self._handle_server_to_client)
        self.s2c_thread.start()

    def _close_sockets(self):
        if self.client_socket is not None:
            self.client_socket.close()
        if self.server_socket is not None:
            self.server_socket.close()
        if self.bind_socket is not None:
            self.bind_socket.close()

    def _wait_for_threads_join(self):
        if self.c2s_thread is not None:
            self.c2s_thread.join()
        if self.s2c_thread is not None:
            self.s2c_thread.join()
        if self.starting_thread is not None:
            self.starting_thread.join()
        self.server_connected = False

    def _connect_to_server(self, retry_count=RETRY_COUNT, retry_interval=RETRY_INTERBAL):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Connecting to the real server ...")
        for i in range(retry_count):
            try:
                self.server_socket.connect(self.server_address)
                break
            except TimeoutError as e:
                if i < retry_count - 1:
                    print(f"An error occurred while connecting to {self.server_address}: retrying {str(i+1)} times ...")
                    time.sleep(retry_interval)
                else:
                    print("connect_to_server() is Failed. error: TimeoutError")
                    return
            except Exception as e:
                print("connect_to_server() is Failed. error: " + str(e))
                return
        self.server_connected = True
        print(f"Connected to the real server {self.server_address}")

    def _handle_client_to_server(self):
        if self.client_socket is None:
            print("Client socket is None")
            return
        while True:
            packet = None
            try:
                packet = self.client_socket.recv(self.PACKET_MAX_SIZE)
            except Exception as e:
                print("recv() from client is failed due to an error: " + str(e))
                break
            if not packet:
                print("recv() from client is failed")
                break
            queueing = False
            if self.packet_hold_status:
                for keyword in self.keywords:
                    if re.search(keyword, packet.decode('utf-8', 'ignore')):
                        print(f"[Data]{datetime.datetime.now()}[ ToSVR ][Pending]: {packet.decode('utf-8', 'ignore')}");
                        self._enqueue_packet(packet)
                        queueing = True
                        break
            if not queueing:
                self._pass_through_client_to_server(packet)
    
    def _handle_server_to_client(self):
        while True:
            packet = None
            try:
                packet = self.server_socket.recv(self.PACKET_MAX_SIZE)
            except Exception as e:
                print("recv() from server is failed due to an error: " + str(e))
                break
            if not packet:
                print("recv() from server is failed")
                break
            self._pass_through_server_to_client(packet)

    def _enqueue_packet(self, packet):
        self.queue.put(packet)

    def _dequeue_packet(self):
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None

    def _pass_through_client_to_server_delayed(self, packet):
        with self.server_sending_lock:
            print(f"[Data]{datetime.datetime.now()}[ ToSVR ][Delayed]: {packet.decode('utf-8', 'ignore')}");
            self.server_socket.sendall(packet)

    def _pass_through_client_to_server(self, packet):
        with self.server_sending_lock:
            if not self.output_only_pending_packets:
                print(f"[Data]{datetime.datetime.now()}[ ToSVR ][PassThr]: {packet.decode('utf-8', 'ignore')}");
            self.server_socket.sendall(packet)

    def _pass_through_server_to_client(self, packet):
        if self.client_socket is None:
            print("Client socket is None")
            return
        if not self.output_only_pending_packets:
            print(f"[Data]{datetime.datetime.now()}[FromSVR][PassThr]: {packet.decode('utf-8', 'ignore')}");
        self.client_socket.sendall(packet)


# ------------------------------------------------------------------------------
# Main (for sample usage)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    packet_holder_ip = "localhost"
    packet_holder_port = 16000
    real_server_ip = "localhost"
    real_server_port = 6000
    packet_holder = PacketHolder()
    packet_holder.register_pending_keyword("333")
    packet_holder.start(packet_holder_ip, packet_holder_port, real_server_ip, real_server_port, wait=True)
