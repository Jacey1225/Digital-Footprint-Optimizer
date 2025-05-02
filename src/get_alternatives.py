from google import genai
import os
import json
import time
import dotenv

#API key used for Gemini services --> .env
env = dotenv.load_dotenv() 
API_KEY = env["API_KEY"]

class GenerateAlternatives:
    def __init_(self, website_url, key=API_KEY):
        self.url = website_url
        self.client = genai.Client(key)

    