OpenAI API Key is not Free to Use so can't use gpt-4o
Using Gemini API Key for the POC

python and pip should be installed
pip install browser-use
playright install

Clone the repo and run the gemini.py locally to test.

Create a .env file in the scripts folder and under GOOGLE_API_KEY place you gemini api key

To run the azure service bus emulator:
- install WSL
- install Docker Desktop or Podman Desktop

in the environment variable set the config.json path and a password
run docker compose -f "path to docker-compose.yml" up -d
                    OR
run podman compose -f "path to docker-compose.yaml" up -ds
verify in Docker Desktop UI and check logs

For Integration with azure service bus emulator install 2 more dependencies
pip install azure-servicebus
pip install azure-identity

The connection String is going to be
"Endpoint=sb://localhost:5672;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"


Few changes that have been done to the subscriptions are
subscription 2 has been set to only contain json's and eventType as ExecuteActionPlan
Subscription 3 has been set to only contain json's and eventType as PythonEngine

Run the azure_service-bus.py file with you modified payload if you want to get the browser use api to automate your task which is action Plan.

Flow of Working
Hardcoded Payload ->-> azure service bus -> pulled to python execution engine -> proccess the message and execute with browser-use -> generate return json ->-> push message to azure service bus 
