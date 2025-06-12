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

Run the azure_service-bus.py file to start the service as a listener, it will keep listening for messages in Subscription.2 and execute them with the LLM agent.

Flow of Working
Run the service bus.py files to run as listener -> run Seperate Script to push message to service bus ->-> listener gets the message and LLM automatically does the job with action plan in message -> Listener returns a message with action status back in to the topic of service bus
