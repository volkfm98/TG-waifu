from Aggregators.IAggregator import AbstractItemIterator


class UserSession:
    """Харнит всю требуемую информацию об одном юзере в течение сессии"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.cur_filter = None
        self.cur_iterator = None