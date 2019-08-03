class ParseBanDurationError(Exception):
    pass


class InvalidCommandError(Exception):
    pass


class InvalidConditionError(Exception):
    pass


class UserAlreadyInStorageError(Exception):
    pass


class UserNotFoundInStorageError(Exception):
    pass


class UserStorageUpdateError(Exception):
    pass
