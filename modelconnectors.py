import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv
import yaml


def create_connection():
    load_dotenv()
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    client = Anthropic()
    model = cfg["claude"]["selection_model"]
    return client, model

def send_message(client, model, prompt):
    try:
        message = client.messages.create(
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        return message
    except anthropic.APIStatusError as e:
        print(e.status_code, e.message, e.body)
        raise
