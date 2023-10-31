import socket
import threading
import sys
import OperationStatus
import re
import HeartBeatThreadClient


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

        # Set later
        self.server_socket_heart_beat: socket.socket | None = None

        self.username: str | None = None
        self.password: str | None = None

        # flag for quit game
        # 退出游戏的标志
        self.quit_game_room_other_exit: bool = False
        # 猜测的标志
        self.on_guessing: bool = False



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


        # 设置心跳的socket
        self.server_socket_heart_beat: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.server_socket_heart_beat.connect((self.server_host, self.server_port))
        except Exception as e:
            print(e)

        # start the client
        # 开始客户端
        self.start()


    def start(self):
        self.login()
        self.game_hall_loop()

    def login(self) -> None:
        """
        The login process
        :return: None
        """
        # STEP Head.0.0.0
        # 要告诉服务器，这是登录的socket
        # tell the server, this is the login socket
        self.server_socket.send("Header:login".encode())

        # STEP Head.0.0.1
        # Received the message from the server, that the server is ready for the command
        self.server_socket.recv(1024).decode()


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
                # print("STEP1.0.2.1", "Client Received")

                # STEP1.0.3.0
                # The result of the login verification
                # 登录验证的结果
                received_message: str = self.server_socket.recv(1024).decode()
                # print("STEP1.0.3.0", received_message)

                # STEP1.0.3.1
                # send msg to the server, I received the message
                self.server_socket.send("Client Received".encode())

                # if the username and password are correct, break the loop
                # 如果用户名和密码正确，退出循环
                if received_message == OperationStatus.OperationStatus.authentication_successful:
                    # 储存用户名
                    # save the username
                    self.username: str = username
                    # 储存密码
                    # save the password
                    self.password: str = password

                    print("Login successful")
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
        # 这个时候要建立心跳链接，定时发送信息，因为如果断开连接，服务器并不知道
        # 新线程
        # 设置心跳
        # print("start setting heart beat")

        # set the heart beat
        heart_beat_thread: HeartBeatThreadClient.HeartBeatThreadClient = HeartBeatThreadClient.HeartBeatThreadClient(
            self.server_socket_heart_beat,
            self,
            self.username
        )

        # start the thread
        # 开始线程
        heart_beat_thread.start()
        # print("finish setting, start heart beat")

        while True:
            # STEP1.1.0.0
            # Receive the message from the server,
            # that the server is ready for the command
            self.server_socket.recv(1024).decode()

            # STEP1.1.0.1
            command = input()
            # prevent for empty command
            # 防止空命令
            # add head "hall_command:" to the command
            # 添加头"hall_command:"到命令
            head: str = "hall_command:"
            command = head + command

            # send the command to the server
            # 发送命令到服务器
            self.server_socket.send(command.encode())

            # STEP1.1.1.0
            # get the server's response, exception or success
            # 获得服务器返回的消息，异常还是成功, for any commands
            received_message: str = self.server_socket.recv(1024).decode()
            print(received_message)


            # if success, break the loop
            # 如果成功
            if received_message == OperationStatus.OperationStatus.wait:

                # STEP 1.1.1.1
                # send msg to the server, I received the message, start to wait
                self.server_socket.send("Client start wait".encode())

                # STEP 1.1.2.0
                # wait for receiving the message from the server
                # Server received
                # 等待服务器通知，游戏开始
                # 创建游戏线程，并等待游戏线程结束
                self.game_loop()
                # after the game, back to the game hall

            # if exit, exit the game
            # 如果退出，退出游戏
            elif received_message == OperationStatus.OperationStatus.bye_bye:
                # STEP1.1.1.1
                # tell the server, I received the message
                self.server_socket.send("Client Received".encode())

                self.server_socket.close()
                sys.exit(0)

            else:
                # STEP1.1.1.1
                # for any other message
                # tell the server, I received the message
                self.server_socket.send("Client Received".encode())



    def game_loop(self):

        # STEP 1.2.0.0
        # wait for receiving the message from the server
        # that the game is started / or the game is finished because someone is out of connection
        # 等待接收服务器的消息，游戏开始/或者游戏结束因为有人断开连接
        # 3012 OR Win
        received_message: str = self.server_socket.recv(1024).decode()
        print(received_message)

        while True:
            # STEP 1.2.0.1
            # input command of guess true or false
            # 输入猜测的命令
            # 设置开始猜测，这样如果收到退出游戏的消息，就会提前让心跳线程打印退出游戏的消息
            self.on_guessing = True
            command: str = input()
            # 设置结束猜测
            self.on_guessing = False

            # flag 不为False，说明有人退出游戏
            # if the flag is not False, it means someone quit the game
            if self.quit_game_room_other_exit:
                # STEP
                # 接受服务器的你赢了消息，游戏结束
                received_message: str = self.server_socket.recv(1024).decode()
                # 但是由于前面心跳线程已经打印了退出游戏的消息，所以这里不用打印
                # but the heart beat thread has already print the message of quit game
                # so here we don't need to print
                # print(received_message)
                break


            # only true/false will send to the server
            # 只有true/false会发送到服务器，true/false不区分大小写
            if matched_user_command := re.fullmatch(r'/guess (?P<guess>[Tt][Rr][Uu][Ee]|[Ff][Aa][Ll][Ss][Ee])', command):
                # get the guess
                # 获得猜测
                guess: str = matched_user_command.group("guess")

                # capitalize the first letter
                # 首字母大写
                guess = guess.capitalize()

                # STEP 1.2.0.1
                # send to the server
                # 发送到服务器
                self.server_socket.send(guess.encode())

                # STEP 1.2.1.0
                # receive the message from the server, RESULT
                # 接收服务器的消息
                received_message: str = self.server_socket.recv(1024).decode()
                # the received message should be the result of the game
                print(received_message)

                # STEP1.2.2.0 (NEED FIX)
                # tell the server, I received the RESULT
                self.server_socket.send("Client Received".encode())

                break

            else:
                print(OperationStatus.OperationStatus.unrecognized_message)

        # back to game hall
        # 回到游戏大厅
        # self.game_hall_loop()



if __name__ == '__main__':
    '''
    if len(sys.argv) != 3:
        print("Usage: python3 GameClient.py <server_host> <server_port>")
        sys.exit(1)

    server_host: str = sys.argv[1]
    server_port: int = int(sys.argv[2])

    game_client: GameClient = GameClient(server_host, server_port)
    '''
    game_client: GameClient = GameClient("localhost", 15210)

