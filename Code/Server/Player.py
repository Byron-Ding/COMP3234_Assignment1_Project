import dataclasses



@dataclasses.dataclass(frozen=True)
class Player:
    user_name: str
    password: str

    user_status: int

    room_id: int = -1


if __name__ == '__main__':
    # test the class
    # 测试类
    player: Player = Player("user_name", "password", 0)
    print(player)
    print(player.user_name)
    print(player.password)
    print(player.user_status)