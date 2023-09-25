import UserInfoFile
import threading
import socket
import sys

import OperationStatus


# Default Encoding is UTF-8


class GameServer:

    def __init__(self, listening_port: int, user_info_file_path: str):
        """
        The Game Server
        :param listening_port:
        :param user_info_file_path: path to a UserInfo.txt file,
         which contains usernames and passwords for all users (clients) that may participate in the application.
        """

        # listening_port is the port the server will listen on
        # user_info_file_path is the path to the file containing the account and password information
        self.listening_port: int = listening_port
        self.account_password_file: str = user_info_file_path

        # create the UserInfoFile object
        self.user_info_file: UserInfoFile = UserInfoFile.UserInfoFile(self.account_password_file)

    # start the server, for handling connections
    # 主线程用于接受连接
    def start(self):
        # When the server start, create a server socket
        # 开始服务器，创建服务器套接字（连接口抽象层）
        server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the server socket to the listening port
        # address is a tuple of (host, port)
        # 将服务器套接字绑定到监听主机名和端口
        # address是一个元组（主机名，端口）
        server_socket.bind(("", self.listening_port))

        # finish creating, and tell which host:port it is
        # Then, listen for connections
        # 完成创建，并告诉它是哪个主机：端口
        # 然后，才能监听链接，要不然会不知道主机在那里
        # listen() has a parameter backlog, the maximum number of connections
        # listen() 有一个参数backlog，最大连接数
        server_socket.listen()

        # accept connections
        # Each TCP connect = a thread
        # 可以循环接受连接了
        # 每个TCP连接 = 一个线程
        while True:
            # accept() returns a tuple of (client_socket, client_address)
            # accept() 返回一个元组（客户端套接字，客户端地址）
            client_accept: tuple = server_socket.accept()
            # create a thread to handle the connection, it does not affect the main thread
            # 分完线程不影响主线程，主线程继续循环接受连接，分线程处理连接
            game_server_thread: GameServerThreadEachPlayer = GameServerThreadEachPlayer(client_accept,
                                                                                        self.user_info_file)
            # start the thread
            # 开始线程
            game_server_thread.start()


class GameServerThreadEachPlayer(threading.Thread):
    """
    The Game Server Thread for handling client connections,
    so that the main thread can continue to accept connections

    The User should First Send the Username and Password to Server
    The Server will Check the Username and Password
    If the Username and Password are Correct, the Server will Send "OK" code to the User

    处理客户端连接子线程，以便主线程可以继续接受连接
    """

    # multiple threads of client connections
    def __init__(self, client_accept: [socket.socket, tuple],
                 user_info_file: UserInfoFile) -> None:
        """
        The Game Server Thread
        :param client_accept: the client accepted, socket.accept()
        """
        super().__init__()

        # User Client Socket
        self.client_socket: socket.socket = client_accept[0]
        # User Client Address
        self.client_address: tuple = client_accept[1]

        # UserInfoFile
        self.user_info_file: UserInfoFile = user_info_file

        '''
        player's status/玩家状态
        0. Reserved Status (Not Used)
        1. Out of House
        2. In the game hall
        3. Waiting in room
        4. Playing a game
        '''
        self.each_player_status: int = 1


    def start(self) -> None:
        """
        Start the thread
        :return: None
        """
        super().start()
        # ——————————————————————————User Login—————————————————————————— #
        # User Login
        # until login successfully or press Ctrl+C
        # 直到登录成功或按Ctrl+C
        login_result: bool = False
        while login_result is not True:
            try:
                login_result = self.login()
            except KeyboardInterrupt:
                # press Ctrl+C
                # 按Ctrl+C
                print("User Press Ctrl+C")
                break
            except Exception as e:
                # other exceptions
                # 其他异常
                print(e)
                break
            else:
                if login_result:
                    # login successfully
                    # 登录成功
                    # send the status code to the client
                    # 将状态码发送给客户端
                    msg: str = OperationStatus.OperationStatus.authentication_successful
                    self.client_socket.send(msg.encode())
                    self.client_socket.send("\n".encode())
                    break
                else:
                    # login failed
                    # 登录失败
                    # send the status code to the client
                    # 将状态码发送给客户端
                    msg: str = OperationStatus.OperationStatus.authentication_failed
                    self.client_socket.send(msg.encode())
                    self.client_socket.send("\n".encode())
                    continue

        # send the message to the client
        # 将消息发送给客户端
        pass

    def run(self):
        ...


    def login(self):
        # ask for the username
        # 请求用户名
        self.client_socket.send("Please input your user name:".encode())
        # wait for the username
        # 等待用户名
        username: str = self.client_socket.recv(1024).decode()
        print(username)
        # ask for the password

        # 请求密码
        self.client_socket.send("Please input your password:".encode())
        # wait for the password
        # 等待密码
        password: str = self.client_socket.recv(1024).decode()
        print(password)

        '''
        After the user has input its password,
        the client sends the user name and password to the server, with a message in the following format
        /login user_name password 
        '''
        #  用户输入密码后，服务端回显用户名和密码至客户端，格式如下
        #  格式 /login user_name password
        #  Do Not Forget to Encode and Decode when Transferring Data
        encoded_username_password: bytes = f"/login {username} {password}\n".encode()
        self.client_socket.send(encoded_username_password)

        # check the username and password
        # 检查用户名和密码
        if self.user_info_file.check_account_password(username, password):
            return True
        else:
            return False



if __name__ == '__main__':
    # create the GameServer object
    # 创建GameServer对象
    # input from the command line by python3 GameServer.py <listening_port> <user_info_file_path>
    # 从命令行输入 python3 GameServer.py <listening_port> <user_info_file_path>
    if len(sys.argv) != 3:
        print("Usage: python3 GameServer.py <listening_port> <user_info_file_path>")
        sys.exit(1)

    # extract tuple
    listening_port: int = int(sys.argv[1])
    user_info_file_path: str = sys.argv[2]

    # create the GameServer
    game_server: GameServer = GameServer(listening_port, user_info_file_path)

    # start the server
    # 开始服务器
    game_server.start()