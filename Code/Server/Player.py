import dataclasses
import socket
import threading
import GameServer


@dataclasses.dataclass()
class Player:
    user_name: str
    password: str

    '''
    player's status/玩家状态
    0. Reserved Status (Not Used)
    1. Out of House
    2. In the game hall
    3. Waiting in room
    4. Playing a game
    '''
    user_status: int

    user_socket: socket.socket

    user_thread: GameServer.GameServerThreadEachPlayer

    game_room: GameServer.GameRoom = None


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


if __name__ == '__main__':
    # test the class
    # 测试类
    player: Player = Player("user_name", "password", 0)
    print(player)
    print(player.user_name)
    print(player.password)
    print(player.user_status)