# packet_holder.py
# Description: This file contains the PacketHolder class, which is used to hold
# packets in a socket channel between a client and a server.
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import collections
import datetime
import queue
import re
from threading import Lock
from threading import Thread
import socket
import time

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# HoldingRule
# ------------------------------------------------------------------------------
class HoldingRule:
    RELEASE_TYPE_NONE = 0
    RELEASE_TYPE_FROM_SERVER = 1
    RELEASE_TYPE_FROM_CLIENT = 2
    def __init__(self, holding_keyword="", release_type=RELEASE_TYPE_NONE, release_keyword="", enabled=False):
        self.holding_keyword = holding_keyword
        self.release_type = release_type
        self.release_keyword = release_keyword
        self.enabled = enabled

    def get_holding_keyword(self):
        return self.holding_keyword
    
    def get_release_type(self):
        return self.release_type
    
    def get_release_keyword(self):
        return self.release_keyword
    
    def is_enabled(self):
        return self.enabled
    
    def set_holding_keyword(self, holding_keyword):
        self.holding_keyword = holding_keyword

    def set_release_type(self, release_type):
        self.release_type = release_type

    def set_release_keyword(self, release_keyword):
        self.release_keyword = release_keyword

    def enable(self):   
        self.enabled = True
    
    def disable(self):
        self.enabled = False

    def __str__(self):
        return f"HoldingRule: holding_keyword={self.holding_keyword}, release_type={self.release_type}, release_keyword={self.release_keyword}, enabled={self.enabled}"
    

# ------------------------------------------------------------------------------
# PacketHolder
# ------------------------------------------------------------------------------
class PacketHolder:
    PACKET_MAX_SIZE = 65536
    RETRY_COUNT = 100
    RETRY_INTERBAL = 3

    def __init__(self, num_of_rules=1):
        self.holding_rules = [HoldingRule() for _ in range(num_of_rules)]
        self.server_sending_lock = Lock()
        self.queue = collections.deque()
        self.queue_lock = Lock()
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
        self.output_only_holding_packets = False

    def set_holding_rule(self, index=0, holding_keyword="", release_type=HoldingRule.RELEASE_TYPE_NONE, release_keyword="", enable=False):
        if index < 0 or index >= len(self.holding_rules):
            print(f"Invalid index: {index}")
            return
        self.holding_rules[index].set_holding_keyword(holding_keyword)
        self.holding_rules[index].set_release_type(release_type)
        self.holding_rules[index].set_release_keyword(release_keyword)
        self.holding_rules[index].enable() if enable else self.holding_rules[index].disable()
    
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
        
    def send_all_holding_packets(self):
        if not self.started:
            print("Process is not started")
            return
        for packet in self._dequeue_packets():
            self._pass_through_client_to_server_delayed(packet)
    
    def set_output_only_holding_packets(self, status):
        if status:
            self.output_only_holding_packets = True
        else:
            self.output_only_holding_packets = False

    def _start_internal(self):
        try:
            print("Creating the proxy server for Packet holding ...")
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
        print("Creating the proxy server for Packet holding is created successfully.")
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
            for holding_rule in self.holding_rules:
                if holding_rule.is_enabled():
                    packet_str = packet.decode('utf-8', 'ignore')
                    if holding_rule is not None and re.search(holding_rule.get_holding_keyword(), packet_str):
                        print(f"[Data]{datetime.datetime.now()}[ ToSVR ][Holding]: {packet_str}")
                        self._enqueue_packet(packet, holding_rule)
                        queueing = True
                        break
            if not queueing:
                self._pass_through_client_to_server(packet)
                for packet in self._dequeue_packets(release_type=HoldingRule.RELEASE_TYPE_FROM_CLIENT, packet=packet):
                    self._pass_through_client_to_server_delayed(packet)
    
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
            for packet in self._dequeue_packets(release_type=HoldingRule.RELEASE_TYPE_FROM_SERVER, packet=packet):
                self._pass_through_client_to_server_delayed(packet)

    def _enqueue_packet(self, packet, holding_rule):
        with self.queue_lock:
            self.queue.append((packet, holding_rule))


    def _dequeue_packets(self, release_type=None, packet=None):
        result = []
        with self.queue_lock:
            new_queue = collections.deque()
            while True:
                qdata = None
                try:
                    qdata = self.queue.popleft()
                except IndexError:
                    break
                if release_type is None:
                    result.append(qdata[0])
                elif packet is None:
                    result.append(qdata[0])
                elif release_type == qdata[1].get_release_type() and re.search(qdata[1].get_release_keyword(), packet.decode('utf-8', 'ignore')):
                    result.append(qdata[0])
                else:
                    new_queue.append(qdata)
            self.queue = new_queue
        return result

    def _pass_through_client_to_server_delayed(self, packet):
        with self.server_sending_lock:
            print(f"[Data]{datetime.datetime.now()}[ ToSVR ][Delayed]: {packet.decode('utf-8', 'ignore')}");
            try:
                self.server_socket.sendall(packet)
            except  ConnectionAbortedError as e:
                print(f"sendall() to server is failed due to an error: {str(e)}")

    def _pass_through_client_to_server(self, packet):
        with self.server_sending_lock:
            if not self.output_only_holding_packets:
                print(f"[Data]{datetime.datetime.now()}[ ToSVR ][PassThr]: {packet.decode('utf-8', 'ignore')}");
            try:
                self.server_socket.sendall(packet)
            except ConnectionAbortedError as e:
                print(f"sendall() to server is failed due to an error: {str(e)}")

    def _pass_through_server_to_client(self, packet):
        if self.client_socket is None:
            print("Client socket is None")
            return
        if not self.output_only_holding_packets:
            print(f"[Data]{datetime.datetime.now()}[FromSVR][PassThr]: {packet.decode('utf-8', 'ignore')}");
            try:
                self.client_socket.sendall(packet)
            except ConnectionAbortedError as e:
                print(f"sendall() to client is failed due to an error: {str(e)}")

# ------------------------------------------------------------------------------
# Main (for sample usage)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    packet_holder_ip = "localhost"
    packet_holder_port = 16000
    real_server_ip = "localhost"
    real_server_port = 6000
    packet_holder = PacketHolder()
    packet_holder.set_holding_rule(index=0, holding_keyword="333", enable=True)
    packet_holder.start(packet_holder_ip, packet_holder_port, real_server_ip, real_server_port, wait=True)
