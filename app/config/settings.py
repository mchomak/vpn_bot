from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Telegram
    bot_token: str = Field(..., alias="BOT_TOKEN")
    webhook_host: str = Field(..., alias="WEBHOOK_HOST")
    webhook_path: str = Field("/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field("", alias="WEBHOOK_SECRET")

    # Web server
    webapp_host: str = Field("0.0.0.0", alias="WEBAPP_HOST")
    webapp_port: int = Field(8080, alias="WEBAPP_PORT")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Links
    support_username: str = Field("support", alias="SUPPORT_USERNAME")
    reviews_link: str = Field("https://t.me/reviews", alias="REVIEWS_LINK")
    rules_link: str = Field("https://telegra.ph/rules", alias="RULES_LINK")
    terms_link: str = Field("https://telegra.ph/terms", alias="TERMS_LINK")

    # VPN config file path
    vpn_config_path: str = Field("vpn_config.json", alias="VPN_CONFIG_PATH")

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_host}{self.webhook_path}"

    class Config:
        env_file = ".env"
        populate_by_name = True


settings = Settings()
