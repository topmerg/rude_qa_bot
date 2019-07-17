class BotUtils():
    def __init__(self):
        self.RUDE_QA_CHAT_ID = -1001424452281

    @staticmethod
    def prepare_query(message):
        """
        Get message without command

        example: prepare_query("/getUser rudeboy from rude qa") -> returns "rudeboy from rude qa"
        """
        return ' '.join(message.text.split()[1:])
