class FallbackEngine:
    def __init__(self, chat_agent):
        self.chat = chat_agent

    def run(self, task, error_msg=""):
        context = f"Teknik bir sorun oluştu. Hata: {error_msg}. Lütfen kullanıcıya yardımcı ol: {task}"
        return self.chat.run(context)
