from pydantic_settings import BaseSettings
from supabase import create_client, Client

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_ANON_KEY: str
    API_V1_STR: str = "/v1"

    class Config:
        env_file = ".env"

settings = Settings()

# Create a single, reusable Supabase client instance
supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY) 