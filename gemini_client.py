import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize GenAI Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")

client = genai.Client(api_key=api_key)
DEFAULT_MODEL = "gemini-1.5-flash"

def generate_text(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Generates text based on a prompt."""
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        return response.text or ""
    except Exception as e:
        # Proper error propagation
        raise RuntimeError(f"Error calling Gemini API: {str(e)}")

def generate_text_stream(prompt: str, model: str = DEFAULT_MODEL):
    """Generates a stream of text chunks based on a prompt."""
    try:
        response_stream = client.models.generate_content_stream(
            model=model,
            contents=prompt,
        )
        for chunk in response_stream:
            yield chunk.text or ""
    except Exception as e:
        raise RuntimeError(f"Error calling Gemini streaming API: {str(e)}")

import time
def generate_text_with_retry(prompt: str, model: str = DEFAULT_MODEL, retries: int = 3, backoff: float = 2.0) -> str:
    """Generates text based on a prompt, retrying with exponential backoff on rate limits."""
    for attempt in range(retries):
        try:
            return generate_text(prompt, model=model)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                if attempt < retries - 1:
                    wait_time = backoff * (2 ** attempt)
                    print(f"Rate limit hit during Gemini API call. Retrying in {wait_time}s... (Attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                    continue
            raise e
    return ""
