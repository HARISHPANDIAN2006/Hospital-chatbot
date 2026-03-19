import requests

class MCPClient:
    def __init__(self, base_url="http://localhost:3333"):
        self.base_url = base_url

    def call(self, tool_name: str, payload: dict):
        response = requests.post(
            f"{self.base_url}/tool/{tool_name}",
            json=payload,  # ← Send payload directly, don't wrap it
            timeout=120
        )
        response.raise_for_status()
        return response.json()