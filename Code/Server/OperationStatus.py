import dataclasses


@dataclasses.dataclass(init=False, frozen=True)
class OperationStatus:

    authentication_successful: str = "1001 Authentication successful"
    authentication_failed: str = "1002 Authentication failed"

    #  3001 number_of_all_rooms number_of_players_in_room_1 ... number_of_players_in_room_n
    all_rooms_status: str = "3001 "
    wait: str = "3011 Wait"
    game_started: str = "3012 Game started. Please guess true or false"
    room_full: str = "3013 The room is full"

    result_is_tie: str = "3023 The result is a tie"
    win_the_game: str = "3021 You are the winner"
    lose_the_game: str = "3022 You lost this game"

    bye_bye: str = "4001 Bye bye"
    unrecognized_message: str = "4002 Unrecognized message"

    def __init__(self):
        pass

