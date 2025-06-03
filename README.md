OpenAI API Key is not Free to Use so can't use gpt-4o
Using Gemini API Key for the POC

python and pip should be installed
pip install browser-use
playright install

Clone the repo and run the gemini.py locally to test.

Create a .env file in the scripts folder and under GOOGLE_API_KEY place you gemini api key

To run the azure service bus emulator:
- install WSL
- install Docker Engine

in the environment variable set the config.json path and a password
run docker compose -f "path to docker-compose.yml" up -d
verify in Docker Desktop UI and check logs

For Integration with azure service bus emulator install 2 more dependencies
pip install azure-servicebus
pip install azure-identity

The connection String is going to be
"Endpoint=sb://localhost:5672;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"
