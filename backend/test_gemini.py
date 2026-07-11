from google.genai import Client

from app.config import settings

client = Client(api_key=(settings.GEMINI_API_KEY or "").strip())


response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello in one sentence."
)

print(response.text)