import socket
import threading



class GameClient:
    def __init__(self, server_host: str, server_port: int):
        """
        The Game Client for connecting to the server
        Use TCP
        :param server_host: the server's host name or IP address
        :param server_port: the server's port it is listening on
        """
        # Use TCP

        # server's host name or IP address
        self.server_host: str = server_host
        # server's port it is listening on
        self.server_port: int = server_port

        # create the socket
        # AF_INET is the address family for IPv4
        # SOCK_STREAM is the socket type for TCP
        # 创建用户端的套接字，客户端连接口抽象层
        # AF_INET是IPv4的地址族
        # SOCK_STREAM是TCP的套接字类型
        self.client_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # connect to the server
        # 连接到服务器，host:port
        # try to connect to the server, Catch exceptions
        # 尝试连接服务器，捕获异常
        try:
            self.client_socket.connect((self.server_host, self.server_port))
        except Exception as e:
            print(e)
