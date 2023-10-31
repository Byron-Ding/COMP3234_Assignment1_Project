import socket
import threading
import time
import OperationStatus
import GameClient


class HeartBeatThreadClient(threading.Thread):

    def __init__(self, server_socket: socket.socket,
                 player_client: GameClient.GameClient,
                 player_name: str,
                 heart_beat_interval: int = 0.5):
        super().__init__()
        # the server socket
        self.server_socket: socket.socket = server_socket
        # the heart beat interval
        self.heart_beat_interval: int = heart_beat_interval
        # the player info
        # 格式是 username:{real_username}
        self.player_name: str = player_name

        self.player_client: GameClient.GameClient = player_client

    def run(self):
        # 定期发送心跳包
        # send heart beat package periodically
        # 先发送玩家信息，用于校验
        # send the player information first, for the verification
        # 发送的格式为：Header:player info:username
        player_info_header: str = "Header:heart beat:{}:client".format(self.player_name.split(":")[1])
        self.server_socket.send(player_info_header.encode())
        print("finish sending 1st heart beat package")

        while True:
            # send the heart beat package
            # 发送心跳包
            # 发送的格式为：Header:heart beat:username
            self.server_socket.send("Heart beat:atrium:send".encode())
            # Receive the message from the server, check both alive
            received_heart_beat: str = self.server_socket.recv(1024).decode()

            # print("finish sending heart beat package NN")
            time.sleep(self.heart_beat_interval)
