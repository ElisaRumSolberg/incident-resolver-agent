import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    google_cloud_project: str = ""
    google_cloud_location: str = "global"
    firestore_database: str = "(default)"
    gemini_model: str = "gemini-3-flash-preview"
    allowed_origins: str = "http://localhost:3000"
    demo_service_url: str = "http://localhost:8080"
    demo_service_id: str = "demo-service"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()

# google-adk's model resolution reads these from the environment directly
# rather than accepting them as constructor args.
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "1")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", settings.google_cloud_project)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", settings.google_cloud_location)
