import GameRoom
import Player


class GameHall:
    DEFAULT_GAME_ROOM_NUMBER = 10

    def __init__(self, game_room_number: int = DEFAULT_GAME_ROOM_NUMBER):
        self.game_room_number: int = game_room_number

        # create the game room list
        # 创建游戏房间列表
        self.game_room_list: [GameRoom.GameRoom] = []

        # Player List
        # 玩家列表
        self.player_list: [Player.Player] = []

        for i in range(self.game_room_number):
            self.game_room_list.append(GameRoom.GameRoom(i))

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

    def enter_room(self, player: Player.Player, room_id: int) -> bool:
        if room_id > self.game_room_number:
            return False
        # player should in the player list


        if player in self.player_list:
            # find the room
            # get into the room
            # if success it will return True
            return self.game_room_list[room_id].add_player(player)

        else:
            return False
