import dataclasses
import socket
import threading
import GameServer


class Player:

    '''
    player's status/玩家状态
    0. Reserved Status (Not Used)
    1. Out of House
    2. In the game hall
    3. Waiting in room
    4. Playing a game
    '''
    RESERVED_STATUS: int = 0
    OUT_OF_HOUSE: int = 1
    IN_THE_GAME_HALL: int = 2
    WAITING_IN_ROOM: int = 3
    PLAYING_A_GAME: int = 4

    def __init__(self,
                 player_name: str,
                 password: str,
                 player_message_socket_channel: socket.socket,
                 player_thread: GameServer.GameServerThreadEachPlayer,
                 player_hear_beat_socket_channel: socket.socket = None,
                 player_status: int = 0
                 ):

        self.player_name: str = player_name
        self.password: str = password
        self.player_socket: socket.socket = player_message_socket_channel
        self.player_thread: GameServer.GameServerThreadEachPlayer = player_thread
        self.player_status: int = player_status
        self.player_heart_beat_socket_channel: socket.socket = player_hear_beat_socket_channel


        self.game_room: GameServer.GameRoom = None



        self.player_status: int
        self.game_room: GameServer.GameRoom = None


        '''
        player's status/玩家状态
        0. Reserved Status (Not Used)
        1. Out of House
        2. In the game hall
        3. Waiting in room
        4. Playing a game
        '''


if __name__ == '__main__':
    # test the class
    # 测试类
    player: Player = Player("player_name", "password", 0, )
    print(player)
    print(player.player_name)
    print(player.password)
    print(player.player_status)