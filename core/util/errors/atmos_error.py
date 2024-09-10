
class UserNamePasswdNotSetError(Exception):
    def __init__(self, user_env):
        super(UserNamePasswdNotSetError, self).__init__(
            f'{user_env} is not set in environment variables'
        )