import threading

import Player
import OperationStatus
import GameServer
import random
import re


class GameRoom:
    DEFAULT_MAX_PLAYER_NUMBER = 2

    def __init__(self, game_server: GameServer.GameServer,
                 room_id: int,
                 max_player_number: int = DEFAULT_MAX_PLAYER_NUMBER) -> None:

        self.game_server: GameServer.GameServer = game_server
        self.room_id: int = room_id
        self.MAX_PLAYER_NUMBER: int = max_player_number

        # create the player list
        # each room 2 players, just record the player name
        self.player_list: list[Player.Player] = []

    def check_full(self) -> bool:
        """
        Check whether the room is full
        :return: True or False
        """
        if len(self.player_list) == self.MAX_PLAYER_NUMBER:
            return True
        else:
            return False

    def add_player(self, player: Player.Player) -> True:
        """
        Add the player to the room
        Check whether is full and the player is already in the room
        Assume the player is in the room and could not add again
        If the room is full, raise the exception
        If success, return True

        :param player: the player
        :return: None
        """
        if self.check_full():
            # the room is full
            raise OperationStatus.RoomFullError("The room is full")
        else:
            self.player_list.append(player)
            player.game_room = self
            return True

    def remove_player(self, player: Player.Player) -> bool:
        """
        Remove the player from the room
        :param player: the player
        :return: None
        """
        if player in self.player_list:
            self.player_list.remove(player)
            return True
        else:
            return False

    def clear_room(self):
        """
        Clear the room
        :return: None
        """
        self.player_list.clear()

    def whether_full(self) -> bool:
        """
        Whether the room is full, the game should start
        :return: True or False
        """
        if len(self.player_list) == self.MAX_PLAYER_NUMBER:
            return True
        else:
            return False

    class Game(threading.Thread):

        def __init__(self, game_server: GameServer.GameServer, room):
            super().__init__()
            self.game_server: GameServer.GameServer = game_server
            self.room: GameRoom = room
            self.player_list = self.room.player_list

        def run(self):
            self.start_game()

        def send_message_to_all(self, message: str):
            whether_error: bool = False
            for player in self.player_list:
                whether_error: bool = self.send_message_to_player_safe(player, message)

            # if any error, means some player is disconnected
            # send msg to other player, you win
            # clear the room
            if whether_error:
                for player in self.player_list:
                    self.send_message_to_player_safe(player, OperationStatus.OperationStatus.win_the_game)

                    # receive the message from the player, the player receive the message
                    # 接收玩家的消息，玩家接收消息
                    player.player_socket.recv(1024).decode()

                # set all player's status to hall
                # 设置所有玩家的状态为大厅
                for player in self.player_list:
                    # finish pause the thread of Hall
                    # 完成暂停大厅的线程
                    player.player_thread.resume_thread_to_game()

                    player.status = Player.Player.IN_THE_GAME_HALL

                # 一定要先释放玩家线程锁，再清空房间，否则玩家列表为空，无法释放锁
                # must release the player thread lock first, then clear the room
                # otherwise the player list is empty, can not release the lock
                # finally, clear the room
                # 最后，清空房间
                self.room.clear_room()

                raise OperationStatus.PlayerNotFoundError("Some player is disconnected")
            # if no error, means all player is connected, CONTINUE
            else:
                return True

        def send_message_to_all_by_heart_channel(self, message: str):
            whether_error: bool = False
            for player in self.player_list:
                whether_error: bool = self.send_message_to_player_safe_by_heart_channel(player, message)
                # heart_beat 是一发一收，发了要立马接受，否则会阻塞
                receive_msg = player.player_heart_beat_socket_channel.recv(1024).decode()

        def receive_message_from_all(self, received_messages: list[str]) -> bool:
            whether_error: bool = False
            for player in self.player_list:
                try:
                    received_message: str = player.player_socket.recv(1024).decode()
                except Exception as e:
                    whether_error: bool = True
                    self.game_server.print_message("Receive message Error:", player, e)
                    break
                else:
                    # add to the list
                    received_messages.append(received_message)

            # if any error, means some player is disconnected
            # send msg to other player, you win
            # clear the room
            if whether_error:
                print(self.player_list)
                for player in self.player_list:
                    print(player.player_name)
                    self.send_message_to_player_safe(player, OperationStatus.OperationStatus.win_the_game)
                    print("finish sending win the game message", player.player_name)

                # receive the message from the player, the player receive the message
                # 接收玩家的消息，玩家接收消息
                # for player in self.player_list:
                #     player.player_socket.recv(1024).decode()

                # set all player's status to hall
                # 设置所有玩家的状态为大厅
                for player in self.player_list:
                    # finish pause the thread of Hall
                    # 完成暂停大厅的线程
                    player.player_thread.resume_thread_to_game()

                    player.status = Player.Player.IN_THE_GAME_HALL

                # clear the room
                # since the game is over
                self.room.clear_room()

                raise OperationStatus.PlayerNotFoundError("Some player is disconnected")
            # if no error, means all player is connected, CONTINUE
            else:
                return True

        # a decorator to check send msg to all player in the room
        # any error will be raised
        # the player will be removed from the room
        # other player will receive a message of win
        def send_message_to_player_safe(self, player: Player.Player, message: str) -> bool:

            """
            Try send the message to a single player, and receive the response
            If failed, remove the player from the room, AND return False
            If success, return True
            :param player:
            :param message:
            :return:
            """

            try:
                # send the message 0
                # get the player's socket
                player.player_socket.send(message.encode())

            except ConnectionError as e:
                self.game_server.print_message("Connection Error:", player.player_name, repr(e))

                # self.room.remove_player(player)
                return True

            except Exception as e:
                self.game_server.print_message("Unknown Error:", player.player_name, repr(e))

                # self.room.remove_player(player)
                return True

            else:
                return False

        # a decorator to check send msg to all player in the room
        # any error will be raised
        # the player will be removed from the room
        # other player will receive a message of win
        def send_message_to_player_safe_by_heart_channel(self, player: Player.Player, message: str) -> bool:

            """
            Try send the message to a single player, and receive the response
            If failed, remove the player from the room, AND return False
            If success, return True
            :param player:
            :param message:
            :return:
            """

            try:
                # send the message 0
                # get the player's socket
                player.player_heart_beat_socket_channel.send(message.encode())
            except ConnectionError as e:
                self.game_server.print_message("Connection Error:", player.player_name, repr(e))

                self.room.remove_player(player)
                return True

            except Exception as e:
                self.game_server.print_message("Unknown Error:", player.player_name, repr(e))

                self.room.remove_player(player)
                return True

            else:
                return False

        @staticmethod
        def generate_random_bool() -> bool:
            """
            Generate a random boolean
            :return: True or False
            """
            return bool(random.getrandbits(1))

        def start_game(self):
            # try:
            # STEP 1.2.0.0
            self.game_server.print_message("Sending game started message......")
            try:
                self.send_message_to_all(OperationStatus.OperationStatus.game_started)
            except Exception as e:
                self.game_server.print_message(e)
                return

            # generate a random boolean
            # 生成一个随机布尔值
            random_bool: bool = self.generate_random_bool()

            # temp variable to store the player's guess
            # 临时变量存储玩家的猜测
            player_guess_str: list[str] = []

            # STEP 1.2.0.1
            # receive the message from the player, the player's guess
            # 接收玩家的消息，猜测
            # 过滤非法命令在用户端进行
            # filter the illegal command is at the client side
            try:
                self.receive_message_from_all(player_guess_str)
            except Exception as e:
                self.game_server.print_message(e)
                return


            self.game_server.print_message(player_guess_str)

            # STEP 1.2.1.0 RESULT
            # if equal, the result is tie
            # 如果相等，结果是平局
            if player_guess_str[0] == player_guess_str[1]:
                try:
                    self.send_message_to_all(OperationStatus.OperationStatus.result_is_tie)
                except Exception as e:
                    # 自带处理异常
                    self.game_server.print_message(e)
                    return

            # if not equal, the result is not tie
            # 如果不相等，结果不是平局
            else:
                # the one who guess the same as the random bool is the winner
                # 猜测和随机布尔值相同的是赢家
                if player_guess_str[0] == str(random_bool):
                    winner: Player.Player = self.player_list[0]
                    loser: Player.Player = self.player_list[1]
                else:
                    winner: Player.Player = self.player_list[1]
                    loser: Player.Player = self.player_list[0]

                # send the message to the winner and loser
                # 发送消息给赢家和输家
                self.send_message_to_player_safe(winner, OperationStatus.OperationStatus.win_the_game)
                self.send_message_to_player_safe(loser, OperationStatus.OperationStatus.lose_the_game)

            # STEP 1.2.2.0 (NEED FIX)
            receive_result: list[str] = []
            try:
                self.receive_message_from_all(player_guess_str)
            except Exception as e:
                self.game_server.print_message(e)
                return

            print(receive_result)

            # set all player's status to hall
            # 设置所有玩家的状态为大厅
            for player in self.player_list:
                # finish pause the thread of Hall
                # 完成暂停大厅的线程
                player.player_thread.resume_thread_to_game()

                player.status = Player.Player.IN_THE_GAME_HALL

            # 一定要先释放玩家线程锁，再清空房间，否则玩家列表为空，无法释放锁
            # must release the player thread lock first, then clear the room
            # otherwise the player list is empty, can not release the lock
            # finally, clear the room
            # 最后，清空房间
            self.room.clear_room()

            # except Exception as e:
            #    self.game_server.print_message(e)
