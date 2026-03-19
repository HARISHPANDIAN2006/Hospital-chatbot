try:
    from mcp.action_router import ActionRouter
    from mcp.intent_classifier import IntentClassifier
except (ModuleNotFoundError, ImportError):
    from action_router import ActionRouter
    from intent_classifier import IntentClassifier

class MCPController:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.router = ActionRouter()

    def decide(self, query: str) -> str:
        intent = self.intent_classifier.classify(query)
        return self.router.route(intent)
