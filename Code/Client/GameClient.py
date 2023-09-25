import socket
import threading
import sys
import OperationStatus



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


        # start the client
        # 开始客户端
        self.start()

    def start(self):
        # Get input for sending
        while True:
            try:
                # username prompt
                # 用户名提示
                received_message: str = self.client_socket.recv(1024).decode()
                print(received_message, end="")

                # input the username
                # 输入用户名
                username: str = input()
                # send the username
                # 发送用户名
                self.client_socket.send(username.encode())

                # password prompt
                # 密码提示
                received_message: str = self.client_socket.recv(1024).decode()
                print(received_message, end="")

                # input the password
                # 输入密码
                password: str = input()
                # send the password
                # 发送密码
                self.client_socket.send(password.encode())

                # verify the username and password and get the result
                # 确认以回显用户名和密码 并获取结果，成功还是失败
                received_message: str = self.client_socket.recv(1024).decode()
                print(received_message, end="")

                # if the username and password are correct, break the loop
                # 如果用户名和密码正确，退出循环
                return_state_msg: str = received_message.split("\n")[1]

                if return_state_msg == OperationStatus.OperationStatus.authentication_successful:
                    break

            except KeyboardInterrupt:
                print('\n')
                print("Terminated abnormally!!")
                self.client_socket.close()
                sys.exit(1)

            except Exception as e:
                print(e)
                self.client_socket.close()
                sys.exit(1)



if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 GameClient.py <server_host> <server_port>")
        sys.exit(1)

    server_host: str = sys.argv[1]
    server_port: int = int(sys.argv[2])

    game_client: GameClient = GameClient(server_host, server_port)
