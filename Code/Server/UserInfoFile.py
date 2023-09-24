import os


class UserInfoFile:

    def __init__(self, path: str):

        # check file exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} does not exist")

        # path is the path to the file
        self.path: str = path

        # accounts is a dictionary of accounts and passwords
        self.accounts: dict[str, str] = {}

        # read the file
        self.read_file()

    def read_file(self):
        """
        Reads the file and stores the accounts and passwords in a dictionary
        Format of file:
            account1:password1
            account2:password2
            account3:password3
            ...

        """
        with open(self.path, "r") as file:
            line: str
            for line in file:
                account, password = line.strip().split(":")
                self.accounts[account] = password

    def check_account_password(self, account: str, password: str) -> bool:
        """
        Checks if the account and password are correct/exist
        """
        if account in self.accounts:
            if self.accounts[account] == password:
                return True
        return False



if __name__ == '__main__':
    # print the accounts and passwords
    apf = UserInfoFile("UserInfo.txt")
    print(apf.accounts)

    # check if the account and password are correct
    print(apf.check_account_password("user1", "user1_password"))
    print(apf.check_account_password("user1", "password2"))
