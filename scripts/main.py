import json
data = {
    "messageId": "12345",
    "eventType": "CreateActionPlan",
    "timestamp": "2025-05-20T12:34:56Z",
    "data": {
        "flowId": "flowId123",
        "userId": "pnl0usXX",
        "nlp": "Login to SNOW and view all tickets in all status",
        "actionPlan": """Open https://aholddelhaize.service-now.com/
Login with user pnl0us72 and password xxxxxxxxx
View all tickets in all status
logout"""
    }
}
print(json.dumps(data, indent=2))