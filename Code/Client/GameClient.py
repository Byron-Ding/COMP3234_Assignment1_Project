import socket
import threading
import sys
import OperationStatus
import re


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
        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # connect to the server
        # 连接到服务器，host:port
        # try to connect to the server, Catch exceptions
        # 尝试连接服务器，捕获异常
        try:
            self.server_socket.connect((self.server_host, self.server_port))
        except Exception as e:
            print(e)


        # start the client
        # 开始客户端
        self.start()

        # the user will do the option and entering commands in the game hall
        self.game_hall_loop()

    def start(self):
        self.login()


    def login(self) -> None:
        """
        The login process
        :return: None
        """
        # Get input for sending
        while True:
            try:
                # username prompt
                # 用户名提示
                # STEP1.0.0.0
                received_message: str = self.server_socket.recv(1024).decode()
                print(received_message, end="")

                # input the username
                # 输入用户名
                username: str = input()
                # Add a head of sending, to allow empty username
                # 添加发送的头，允许空用户名
                username = "username:" + username
                # send the username
                # 发送用户名
                # STEP1.0.0.1
                self.server_socket.send(username.encode())


                # STEP1.0.1.0
                # password prompt
                # 密码提示
                received_message: str = self.server_socket.recv(1024).decode()
                print(received_message, end="")

                # input the password
                # 输入密码
                password: str = input()
                # Add a head of sending, to allow empty password
                # 添加发送的头，允许空密码
                password = "password:" + password
                # send the password
                # STEP1.0.1.1
                # 发送密码
                self.server_socket.send(password.encode())


                # STEP1.0.2.0
                # show username and password, to let user comfirm
                # 显示用户名和密码，方便用户确认
                received_message: str = self.server_socket.recv(1024).decode()
                print(received_message, end="")

                # STEP1.0.2.1
                # send msg to the server, I received the message
                self.server_socket.send("Client Received".encode())


                # STEP1.0.3.0
                # The result of the login verification
                # 登录验证的结果
                received_message: str = self.server_socket.recv(1024).decode()
                print(received_message)

                # STEP1.0.3.1
                # send msg to the server, I received the message
                self.server_socket.send("Client Received".encode())

                # if the username and password are correct, break the loop
                # 如果用户名和密码正确，退出循环
                if received_message == OperationStatus.OperationStatus.authentication_successful:
                    break

            except KeyboardInterrupt:
                print('\n')
                print("Terminated abnormally!!")
                self.server_socket.close()
                sys.exit(1)

            except Exception as e:
                print(e)
                self.server_socket.close()
                sys.exit(1)

    def game_hall_loop(self):
        command: str
        while True:
            # STEP1.1.0.0
            # Receive the message from the server,
            # that the server is ready for the command
            self.server_socket.recv(1024).decode()

            # STEP1.1.0.1
            command = input()
            # send the command to the server
            # 发送命令到服务器
            self.server_socket.send(command.encode())

            # get the server's response
            # 获得服务器返回的消息
            received_message: str = self.server_socket.recv(1024).decode()
            print(received_message)



if __name__ == '__main__':
    '''
    if len(sys.argv) != 3:
        print("Usage: python3 GameClient.py <server_host> <server_port>")
        sys.exit(1)

    server_host: str = sys.argv[1]
    server_port: int = int(sys.argv[2])

    game_client: GameClient = GameClient(server_host, server_port)
    '''
    game_client: GameClient = GameClient("localhost", 3)

