import Player


class GameRoom:
    DEFAULT_MAX_PLAYER_NUMBER = 2

    def __init__(self, room_id: int, max_player_number: int = DEFAULT_MAX_PLAYER_NUMBER) -> None:

        self.room_id: int = room_id
        self.MAX_PLAYER_NUMBER: int = max_player_number

        # create the player list
        # each room 2 players, just record the player name
        self.player_list: list[Player.Player, Player.Player] = []

    def add_player(self, player: Player.Player) -> bool:
        """
        Add the player to the room
        :param player: the player
        :return: None
        """
        if len(self.player_list) >= self.MAX_PLAYER_NUMBER:
            return False
        else:
            self.player_list.append(player)
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

