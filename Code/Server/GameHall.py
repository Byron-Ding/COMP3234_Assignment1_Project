import GameRoom
import Player
import OperationStatus
import GameServer
import socket


class GameHall:
    DEFAULT_GAME_ROOM_NUMBER = 10

    def __init__(self,
                 game_server: GameServer.GameServer,
                 game_room_number: int = DEFAULT_GAME_ROOM_NUMBER) -> None:
        self.game_room_number: int = game_room_number

        # create the game room list
        # 创建游戏房间列表
        self.game_room_list: [GameRoom.GameRoom] = []
        # the room starts the game
        self.active_room_list: [GameRoom.GameRoom] = []

        # Player List
        # 玩家列表
        self.player_list: [Player.Player] = []

        for i in range(self.game_room_number):
            self.game_room_list.append(GameRoom.GameRoom(game_server, i))

    def add_player(self, player: Player.Player) -> bool:

        if player in self.player_list:
            return False
        else:
            self.player_list.append(player)
            return True

    def remove_player(self, player: Player.Player) -> bool:

        if player in self.player_list:
            self.player_list.remove(player)
            return True
        else:
            return False

    def enter_room(self, player: Player.Player, room_id: int) -> True:
        """
        Enter the room
        if success, return True
        if failed, raise the exception depends on the reason

        :param player: the player Object
        :param room_id: the room id
        :return:
        """
        # room id should be in the room list, not out of range
        # notice that the room id is start from 0, so the max room id is game_room_number - 1
        if room_id >= self.game_room_number:
            raise OperationStatus.InvalidOperationError("The room id is out of range")

        # player should in the player list
        if player in self.player_list:
            # find the room
            # get into the room
            # if success it will return True
            self.game_room_list[room_id].add_player(player)
            return True
        else:
            raise OperationStatus.PlayerNotFoundError("The player is not in the player list")

    def list_room_and_status(self) -> str:
        """
        return a string showing the room status
        the format is
        3001 number_of_all_rooms number_of_players_in_room_1 ... number_of_players_in_room_n
        """
        # create list
        # [3001, number of all rooms, number of players in room 1, ... number of players in room n]
        # head, total information
        output_list: list[int | str] = [OperationStatus.OperationStatus.list_rooms_status,
                                        self.game_room_number]
        # room status list
        room_status_list: list[int] = [len(each_room.player_list) for each_room in self.game_room_list]

        # final combined list
        output_list.extend(room_status_list)

        # convert to string
        output_str: str = " ".join([str(each) for each in output_list])

        return output_str

    # 对应心跳包
    # 按照名字找到玩家，然后把心跳包的socket赋值给玩家的socket
    def correspond_heart_beating_socket_to_player_socket(self,
                                                         player_name: str,
                                                         heart_beating_socket: socket.socket) -> bool:

        player: Player.Player
        for player in self.player_list:
            if player.player_name == player_name:
                player.player_heart_beat_socket_channel = heart_beating_socket
                return True

        return False

    # 查看有没有对应的玩家
    def get_player_by_username(self, user_name: str) -> Player.Player | None:
        player: Player.Player
        for player in self.player_list:
            if player.player_name == user_name:
                return player

        return None
