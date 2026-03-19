class ActionRouter:
    def route(self, intent: str) -> str:
        if intent == "KNOWLEDGE_QUERY":
            return "RUN_RAG"

        if intent in {
            "REGISTER_PATIENT",
            "BOOK_APPOINTMENT",
            "GET_APPOINTMENTS",
            "SEARCH_DOCTORS",
        }:
            return "RUN_MCP"

        return "UNKNOWN"
