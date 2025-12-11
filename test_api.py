from google import genai
from dotenv import load_dotenv

load_dotenv()

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash-lite", contents="how to play basketball"
)
print(response.text)