import UserInfoFile
import threading
import socket
import sys
import re
import random

import OperationStatus
import GameHall
import Player



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


        # create Game Hall,
        # do not create in the thread,
        # or there will be multiple game halls,
        # the user should be in the same game hall
        # 创建游戏大厅，不要在线程里创建，不然会出现多个游戏大厅，用户应该在同一个游戏大厅
        self.game_hall: GameHall.GameHall = GameHall.GameHall()

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
        server_socket.listen(100)

        # accept connections
        # Each TCP connect = a thread
        # 可以循环接受连接了
        # 每个TCP连接 = 一个线程
        while True:
            # accept() returns a tuple of (server_socket, client_address)
            # accept() 返回一个元组（客户端套接字，客户端地址）
            client_accept: tuple = server_socket.accept()
            # create a thread to handle the connection, it does not affect the main thread
            # 分完线程不影响主线程，主线程继续循环接受连接，分线程处理连接
            game_server_thread: GameServerThreadEachPlayer = GameServerThreadEachPlayer(client_accept,
                                                                                        self)
            # start the thread
            # 开始线程
            game_server_thread.start()


class Game(threading.Thread):
    """
    For all rooms, when a room is full, start a game as a new thread, thread finishes when the game is over
    """
    def __init__(self, game_room: GameHall.GameRoom):
        super().__init__()
        self.game_room: GameHall.GameRoom = game_room
        self.player_list: list[Player.Player] = game_room.player_list

    def start(self) -> None:
        super().start()

    def run(self) -> None:
        """
        Start the thread, Start the game
        The whole game process is defined here
        After the last player enters the Room, pass the Game room object to here, and start the game.
        The Game Room object has 2 players socket, and the game room id, which could be used to send the message
        and auto exit 2 players from the game room after the game is finished
        :return: None
        """


    # 生成随机的布尔值
    # generate random bool
    def generate_random_bool(self) -> bool:
        return random.choice([True, False])


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
                 game_server: GameServer) -> None:
        """
        The Game Server Thread
        :param client_accept: the client accepted, socket.accept()
        """
        super().__init__()

        # User Client Socket
        self.player: Player.Player | None = None
        self.client_socket: socket.socket = client_accept[0]
        # User Client Address
        self.client_address: tuple = client_accept[1]

        # Game Server, For all shared resources, including the game hall
        self.game_server: GameServer = game_server

        # UserInfoFile
        self.user_info_file: UserInfoFile = game_server.user_info_file


    def start(self) -> None:
        """
        Start the thread
        :return: None
        """
        super().start()

    def run(self) -> None:
        """
        Start the thread
        :return: None
        """
        # super().start()
        # start only execute 1 time each thread, and after it finish executing, a new thread will be created
        # so do not use start
        # ——————————————————————————User Login—————————————————————————— #
        # User Login
        # until login successfully or press Ctrl+C
        # 直到登录成功或按Ctrl+C
        self.login()
        # ——————————————————————————User Login—————————————————————————— #

        # ——————————————————————————Game Hall—————————————————————————— #
        self.game_hall()
        # ——————————————————————————Game Hall—————————————————————————— #


    def login(self) -> None:
        login_result: bool = False
        while login_result is not True:
            try:
                # STEP1.0.0.0 - 1.0.2.1
                login_result = self.login_process()
                # STEP1.0.3.0 - 1.0.3.1
                self.login_result_response(login_result)

                # if login successfully, then enter the game hall
                # 如果登录成功，则进入游戏大厅
                if login_result:
                    break

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

    def login_process(self):
        """
        Login, ask for the username and password, and check the username and password
        登录，请求用户名和密码，并检查用户名和密码

        :return: Whether the login is successful
        """
        # ask for the username
        # 请求用户名
        # STEP1.0.0.0
        self.client_socket.send("Please input your user name:".encode())
        # wait for the username
        # 等待用户名
        # STEP1.0.0.1
        username: str = self.client_socket.recv(1024).decode()
        # del the head, the format is username:username
        # 删除头，格式 username:username
        # Allow empty username
        username = username[9:]
        print(username)
        # ask for the password

        # 请求密码
        # STEP1.0.1.0
        self.client_socket.send("Please input your password:".encode())
        # wait for the password
        # STEP1.0.1.1
        # 等待密码
        password: str = self.client_socket.recv(1024).decode()
        # del the head, the format is password:password
        # 删除头，格式 password:password
        # Allow empty password
        password = password[9:]
        print(password)

        '''
        After the user has input its password,
+         /login user_name password 
        '''
        # STEP1.0.2.0
        #  用户输入密码后，服务端回显用户名和密码至客户端，格式如下
        #  格式 /login user_name password
        #  Do Not Forget to Encode and Decode when Transferring Data
        encoded_username_password: bytes = f"/login {username} {password}\n".encode()
        self.client_socket.send(encoded_username_password)
        # STEP1.0.2.1
        # wait for the result, whether the user accept the message
        # 等待结果，用户是否接受消息
        received_message: str = self.client_socket.recv(1024).decode()
        # here, the received_message should be "Received"


        # check the username and password
        # 检查用户名和密码
        if self.user_info_file.check_account_password(username, password):
            # if login successfully, then enter the game hall
            # 如果登录成功，则进入游戏大厅
            # if the username and password are correct, create a player object
            '''
            player's status/玩家状态
            0. Reserved Status (Not Used)
            1. Out of House
            2. In the game hall
            3. Waiting in room
            4. Playing a game
            '''
            self.player: Player.Player = Player.Player(user_name=username,
                                                       password=password,
                                                       user_status=2,
                                                       user_socket=self.client_socket)
            # add the player to the game hall
            # 将玩家添加到游戏大厅
            # get the shared resource, the game hall
            # 向上调用，获取共享资源，游戏大厅
            self.game_server.game_hall.add_player(self.player)

            return True
        else:
            return False

    def login_result_response(self, login_result: bool) -> None:
        """
        Send the login result to the client
        将登录结果发送给客户端

        :param login_result: Whether the login is successful
        :return: None
        """
        if login_result:
            # login successfully
            # 登录成功
            # send the status code to the client
            # 将状态码发送给客户端
            # STEP1.0.3.0
            msg: str = OperationStatus.OperationStatus.authentication_successful
            self.client_socket.send(msg.encode())
            # STEP1.0.3.1
            # receive the message from the client, check the message is reached
            # 接收客户端的消息，检查消息是否到达
            self.client_socket.recv(1024).decode()

        else:
            # login failed
            # 登录失败
            # send the status code to the client
            # 将状态码发送给客户端
            # STEP1.0.3.0
            msg: str = OperationStatus.OperationStatus.authentication_failed
            self.client_socket.send(msg.encode())
            # STEP1.0.3.1
            # receive the message from the client, check the message is reached
            # 接收客户端的消息，检查消息是否到达
            self.client_socket.recv(1024).decode()

    def game_hall(self):
        # wait for the user to choose the operation
        # 等待用户选择操作
        while True:
            # STEP1.1.0.0
            # sent the error_msg to the client, say you are ready to send the command
            # 将消息发送给客户端，表示你可以发送命令了
            self.client_socket.send("Server Ready".encode())

            # get the command
            # 获取命令
            # STEP1.1.0.1
            user_command: str = self.client_socket.recv(1024).decode()
            # del the head, the format is hall_command:command
            # 删除头，格式 hall_command:command
            user_command = user_command[13:]

            # /list to list all the rooms
            # output return format is
            # 3001 number_of_all_rooms number_of_players_in_room_1 ... number_of_players_in_room_n
            # if the command is valid
            if user_command == "/list":
                # get the room status
                # 获取房间状态
                room_status: str = self.game_server.game_hall.list_room_and_status()

                # send the command to the server
                # 将命令发送给服务器
                # STEP1.1.1.0
                self.client_socket.send(room_status.encode())
                # ensure the client received the message, the msg is "Client Received"
                # 确保客户端收到消息，消息是"Client Received"
                # STEP1.1.1.1
                self.client_socket.recv(1024).decode()

            elif matched_command := re.fullmatch(r"/enter (?P<target_room_number>\d+)", user_command):
                # command should be in /enter <target_room_number>
                # get the target room number
                room_number_enter: int = int(matched_command.group("target_room_number"))

                # enter the room
                # 进入房间
                try:
                    # if the room is full,
                    status = self.game_server.game_hall.enter_room(self.player, room_number_enter)

                except OperationStatus.InvalidOperationError as e:
                    # if the room number is out of range, invalid room number
                    # 如果房间号超出范围，非法房间号
                    error_msg: str = OperationStatus.OperationStatus.unrecognized_message
                    # STEP1.1.1.0
                    self.client_socket.send(error_msg.encode())
                except OperationStatus.RoomFullError as e:
                    # if the room is full
                    # 如果房间已满
                    error_msg: str = OperationStatus.OperationStatus.room_full
                    # STEP1.1.1.0
                    self.client_socket.send(error_msg.encode())
                except Exception as e:
                    error_msg: str = repr(e)
                    # STEP1.1.1.0
                    self.client_socket.send(error_msg.encode())
                else:
                    # if nothing wrong, send msg to the Client that successfully enter the room
                    # break the loop, exit the game hall
                    # 如果没有问题，发送消息给客户端，成功进入房间，退出游戏大厅循环
                    # send the result status code to the client
                    # 将结果状态码发送给客户端
                    msg: str = OperationStatus.OperationStatus.wait
                    # STEP1.1.1.0
                    self.client_socket.send(msg.encode())
                    # although here is a break, the "finally" block will still be executed
                    break

                finally:
                    # ensure the client received the message, the msg is "Client Received"
                    # 确保客户端收到消息，消息是"Client Received"
                    # STEP1.1.1.1
                    self.client_socket.recv(1024).decode()

            else:
                # unrecognized command
                # 未识别的命令
                error_msg: str = OperationStatus.OperationStatus.unrecognized_message
                # STEP1.1.1.0
                self.client_socket.send(error_msg.encode())
                # ensure the client received the message, the msg is "Client Received"
                # 确保客户端收到消息，消息是"Client Received"
                # STEP1.1.1.1
                self.client_socket.recv(1024).decode()

if __name__ == '__main__':
    '''
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
    '''


    # create the GameServer
    game_server: GameServer = GameServer(15210, "UserInfo.txt")

    # start the server
    # 开始服务器
    game_server.start()
