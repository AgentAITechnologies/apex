class PromptError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ConversationNodeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ConversationEdgeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ExecError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class UIError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class LLMAPIRateLimitError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class LLMAPIInternalServerError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class APIKeyError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class TestError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)