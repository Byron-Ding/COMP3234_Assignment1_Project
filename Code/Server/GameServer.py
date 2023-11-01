import UserInfoFile
import threading
import socket
import sys
import re
import random

import OperationStatus
import GameHall
import Player
import GameRoom

# Default Encoding is UTF-8

# Condition Variable for whether heart beat is established
# 心跳是否建立的条件变量
HEART_BEAT_CONDITION_VARIABLE: threading.Condition = threading.Condition()


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
        self.game_hall: GameHall.GameHall = GameHall.GameHall(self)

        # record all threads of the game server, one thread means one client

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

    @staticmethod
    def print_message(*args):
        """
        Print the message
        :param message: the message
        :return: None
        """
        print(args)

    @staticmethod
    def player_connection_error(player: Player, exception: Exception):
        print("Player Connection Error", player.player_name, exception)


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

        # Thread pause flag
        self.thread_lock: threading.Event = threading.Event()
        # Thread pause flag is False, the thread is running
        # Thread pause flag is True, the thread is paused
        self.thread_lock.set()

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
        # —————————————————————————— 区分信息 —————————————————————————— #
        # STEP Head.0.0.0
        # 接受头文件，区分是登录还是心跳包
        # receive the header, to distinguish whether it is login or heart beat package
        header: str = self.client_socket.recv(1024).decode()
        print(header)
        # STEP Head.0.0.1
        # Send Recv
        self.client_socket.send("Received".encode())

        if header == "Header:login":
            # if it is login
            # 如果是登录
            # ——————————————————————————User Login—————————————————————————— #
            # User Login
            # until login successfully or press Ctrl+C
            # 直到登录成功或按Ctrl+C
            self.login()
            # ——————————————————————————User Login—————————————————————————— #

            try:
                # ——————————————————————————Game Hall—————————————————————————— #
                self.game_hall()
                # ——————————————————————————Game Hall—————————————————————————— #
            except ConnectionError as e:
                self.game_server.print_message("Connection Error: " + repr(e) + " player_name: " + self.player.player_name)

            except OperationStatus.PlayerNormalQuit as e:
                self.game_server.print_message(
                    "Player Normal Quit: " + repr(e) + " player_name: " + self.player.player_name)

                # 还是要结束socket
                # close the socket
                self.player.player_socket.close()

            except Exception as e:
                self.game_server.print_message("Unknown Error: " + repr(e) + " player_name: " + self.player.player_name)

        elif header_matched := re.fullmatch(r"Header:heart beat:(?P<username>\w+):client", header):
            # if it is heart beat package
            # 如果是心跳包
            # ——————————————————————————Heart Beat—————————————————————————— #
            # Heart Beat
            # STEP Head.0.0.1
            # 接受心跳包，回显
            # receive the heart beat package, and echo it
            username: str = header_matched.group("username")
            print(f"Heart Beat from", username, "start")
            # 调用GameHall的方法，将心跳包的socket传入
            # call the method of GameHall, pass the heart beat socket
            print("Heart skt is:", self.client_socket is None)
            print(self.game_server.game_hall.correspond_heart_beating_socket_to_player_socket(username,
                                                                                              self.client_socket))
            self.player = self.game_server.game_hall.get_player_by_username(username)
            print(self.player.player_name)
            print(self.game_server.game_hall.get_player_by_username(username).player_heart_beat_socket_channel is None)
            # 心跳包建立后，广播恢复线程，但是要先获取锁
            # After the heart beat is established, broadcast to resume the thread, but need to get the lock first
            # HEART_BEAT_CONDITION_VARIABLE.acquire(blocking=False)

            print("Corresponding Heart Beat Socket to Player Socket Finished")

            # 广播恢复线程
            # broadcast to resume the thread
            # HEART_BEAT_CONDITION_VARIABLE.notify_all()

            # 设置超时时间为1秒
            # set the timeout to 1 second
            self.client_socket.settimeout(1)
            try:
                while True:
                    self.client_socket.recv(1024)
                    # tell the client, the message is received
                    self.client_socket.send("Heart beat:ventricle:response".encode())

            except Exception as e:
                print("Heart Beat Connection Error", e, self.player.player_name)


                # 判断玩家是否在房间里
                # check whether the player is in the room
                if self.player.player_status == Player.Player.PLAYING_A_GAME or \
                        self.player.player_status == Player.Player.WAITING_IN_ROOM:
                    # if the player is in the room, remove the player from the room
                    # 如果玩家在房间里，将玩家从房间里移除
                    self.player.game_room.remove_player(self.player)

                    # remove the player from the game hall
                    # 将玩家从游戏大厅移除
                    self.game_server.game_hall.remove_player(self.player)
                    
                    # 移除socket
                    # remove the socket
                    self.player.player_socket.close()
                    self.player.player_heart_beat_socket_channel.close()

                    # 杀死线程
                    # kill the thread
                    # self.player.player_thread.join()

                    # 退出线程
                    # exit the thread
                    sys.exit(0)



            # ——————————————————————————Heart Beat—————————————————————————— #

        # —————————————————————————— 区分信息 —————————————————————————— #

    def resume_thread_to_game(self) -> None:
        """
        Resume the thread, the game is finished, back to the game hallf
        :return: None
        """
        self.thread_lock.set()

    def stop_thread(self) -> None:
        """
        Stop the thread
        :return: None
        """
        print(self.player.player_name, "Thread Paused")
        self.thread_lock.clear()
        self.thread_lock.wait()
        print(self.player.player_name, "Thread Recovered")

    def send_message(self, message: str):
        try:
            # send the message 0
            self.client_socket.send(message.encode())
        except Exception as e:
            print("Message Send Error", e)

    def login(self) -> None:
        login_result: bool = False
        while login_result is not True:
            try:
                # STEP1.0.0.0 - 1.0.2.1
                # 这一步已经创建玩家实体，加入了大厅
                login_result = self.login_process()
                # STEP1.0.3.0 - 1.0.3.1
                self.login_result_response(login_result)

                # 阻塞线程，直到获取到心跳包的socket
                # HEART_BEAT_CONDITION_VARIABLE.acquire(blocking=True)
                print("Finish Login")
                # if login successfully, then enter the game hall
                # 如果登录成功，则进入游戏大厅
                if login_result:
                    # 进入大厅前要建立心跳链接
                    # 等待建立心跳链接
                    print("Waiting for Heart Beat to be Established")
                    # wait for the heart beat to be established
                    print(self.player.player_name)
                    while self.game_server. \
                            game_hall. \
                            get_player_by_username(self.player.player_name). \
                            player_heart_beat_socket_channel is None:


                        # HEART_BEAT_CONDITION_VARIABLE.wait()
                        pass

                    print("Heart Beat Established")
                    break

            except KeyboardInterrupt as e:
                # press Ctrl+C
                # 按Ctrl+C
                print("Login: User Press Ctrl+C", e)
                break
            except Exception as e:
                # other exceptions
                # 其他异常
                print("Login: Unknown Error:", e)
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
        self.send_message("Please input your user name:")
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
        self.send_message("Please input your password:")
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
+         /login player_name password 
        '''
        # STEP1.0.2.0
        #  用户输入密码后，服务端回显用户名和密码至客户端，格式如下
        #  格式 /login player_name password
        #  Do Not Forget to Encode and Decode when Transferring Data
        encoded_username_password: str = f"/login {username} {password}\n"
        self.send_message(encoded_username_password)
        # STEP1.0.2.1
        # wait for the result, whether the user accept the message
        # 等待结果，用户是否接受消息
        received_message: str = self.client_socket.recv(1024).decode()
        # here, the received_message should be "Received"

        print(received_message)
        print(self.user_info_file.check_account_password(username, password))

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
            # 心跳频道之后建立
            self.player: Player.Player = Player.Player(username,
                                                       password,
                                                       self.client_socket,
                                                       self,
                                                       player_status=1)

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
            self.send_message(msg)
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
            self.send_message(msg)
            # STEP1.0.3.1
            # receive the message from the client, check the message is reached
            # 接收客户端的消息，检查消息是否到达
            self.client_socket.recv(1024).decode()

    def game_hall(self):
        # wait for the user to choose the operation
        # 等待用户选择操作
        print(self.player.player_name, "Game Hall Enter")

        while True:
            # STEP1.1.0.0
            # sent the error_msg to the client, say you are ready to send the command
            # 将消息发送给客户端，表示你可以发送命令了
            self.send_message("STEP1.1.0.0 Server Ready")

            # get the command
            # 获取命令
            # STEP1.1.0.1
            user_command: str = self.client_socket.recv(1024).decode()
            # del the head, the format is hall_command:command
            # 删除头，格式 hall_command:command
            print(user_command)
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
                self.send_message(room_status)
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
                    # if the room is full, raise the exception
                    # if the room is full after join, a game will start, game room obj will be returned
                    whether_successful: bool = self.game_server.game_hall.enter_room(self.player, room_number_enter)

                except OperationStatus.InvalidOperationError as e:
                    # if the room number is out of range, invalid room number
                    # 如果房间号超出范围，非法房间号
                    error_msg: str = OperationStatus.OperationStatus.unrecognized_message
                    # STEP1.1.1.0
                    self.send_message(error_msg)
                except OperationStatus.RoomFullError as e:
                    # if the room is full
                    # 如果房间已满
                    error_msg: str = OperationStatus.OperationStatus.room_full
                    # STEP1.1.1.0
                    self.send_message(error_msg)

                    # ensure the client received the message, the msg is "Client Received"
                    # 确保客户端收到消息，消息是"Client Received"
                    # STEP1.1.1.1
                    self.client_socket.recv(1024).decode()
                except Exception as e:
                    error_msg: str = repr(e)
                    # STEP1.1.1.0
                    self.send_message(error_msg)

                    # ensure the client received the message, the msg is "Client Received"
                    # 确保客户端收到消息，消息是"Client Received"
                    # STEP1.1.1.1
                    self.client_socket.recv(1024).decode()
                else:
                    # if nothing wrong, send msg to the Client that successfully enter the room
                    # break the loop, exit the game hall
                    # 如果没有问题，发送消息给客户端，成功进入房间，退出游戏大厅循环
                    # send the result status code to the client
                    # 将结果状态码发送给客户端
                    msg: str = OperationStatus.OperationStatus.wait
                    # STEP1.1.1.0
                    self.send_message(msg)
                    # change the user status to waiting in room
                    '''
                    player's status/玩家状态
                    0. Reserved Status (Not Used)
                    1. Out of House
                    2. In the game hall
                    3. Waiting in room
                    4. Playing a game
                    '''
                    self.player.player_status = 3
                    # although here is a break, the "finally" block will still be executed

                    # the client tell server start to wait
                    # 客户端告诉服务器开始等待
                    # STEP 1.1.1.1
                    start_wait_msg: str = self.client_socket.recv(1024).decode()
                    print(self.player.player_name, start_wait_msg)

                    # start the game
                    # 开始游戏，有可能判定失败, wait
                    self.start_game()

            elif user_command == "/exit":
                # if the user want to exit the game hall
                # 如果用户想退出游戏大厅
                # send the result status code to the client
                # 将结果状态码发送给客户端
                msg: str = OperationStatus.OperationStatus.bye_bye
                # STEP1.1.1.0
                self.send_message(msg)

                # out of the game hall loop
                # 退出游戏大厅循环
                raise OperationStatus.PlayerNormalQuit("Player Normal Quit")

            else:
                # unrecognized command
                # 未识别的命令
                error_msg: str = OperationStatus.OperationStatus.unrecognized_message
                # STEP1.1.1.0
                self.send_message(error_msg)
                # ensure the client received the message, the msg is "Client Received"
                # 确保客户端收到消息，消息是"Client Received"
                # STEP1.1.1.1
                self.client_socket.recv(1024).decode()

    def start_game(self):
        game_room: GameRoom.GameRoom = self.player.game_room

        # None raise the exception
        if game_room is None:
            raise OperationStatus.InvalidOperationError("The player is not in any room")

        print("Current GameRoom:", game_room.room_id, game_room.check_full())

        # After the last player enter the room, the game will start
        if game_room.check_full():
            print("Game Created")
            game_thread: GameRoom.GameRoom.Game = game_room.Game(self.game_server, game_room)
            print("Game Started")
            # Send msg that the game start to all players
            # STEP 1.2.0.0 [INSIDE FUNCTION BELLOW]
            game_thread.start()

        print("try to pause the thread")
        # pause the thread, wait for the game to finish
        # 暂停线程，等待游戏结束
        self.stop_thread()


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
