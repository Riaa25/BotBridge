import json

class PersonalAgent:
    def __init__(self, name, constraints, client):
        self.name = name
        self.constraints = constraints
        self.client = client

    def negotiate(self, chat_history):
        system_prompt = f"""
        You are {self.name}'s AI Assistant. 
        SECRET NOTES: {self.constraints}
        GOAL: Reach a group agreement FAST. 
        RESPONSE FORMAT (JSON ONLY):
        {{
            "message": "Public message",
            "proposal": "The plan",
            "status": "ACCEPT" or "COUNTER"
        }}
        """
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"History: {chat_history}"}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)