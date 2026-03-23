#환경변수와 기본 설정을 관리하는 파일
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DDI Chatbot"
    version: str = "0.1.0"
    debug: bool = True

    use_llm: bool = False

    factchat_api_key: str = ""
    factchat_base_url: str = "https://factchat-cloud.mindlogic.ai/v1/api/openai"
    factchat_model: str = "gpt-4o-mini"

    # DDI 데이터 소스 설정
    ddi_data_source: str = "seed"   # seed | dur
    dur_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()