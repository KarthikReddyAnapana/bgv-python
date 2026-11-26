from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment variables override these defaults; .env is resolved from the working directory.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret: str = "ChangeThisSecretKeyForPortfolioDevelopmentOnlyMustBe256BitsLong!!"
    jwt_expiration_ms: int = 86_400_000
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175"
    database_url: str = "sqlite:///./data/bgverificationdb.sqlite"
    country_georegion_mapping: str = (
        "USA:USA_AND_CANADA,CANADA:USA_AND_CANADA,MEXICO:USA_AND_CANADA,INDIA:APAC,"
        "POLAND:EUROPE,NETHERLANDS:EUROPE,UNITED_KINGDOM:EUROPE,COSTA_RICA:LATAM,"
        "BRAZIL:LATAM,COLOMBIA:LATAM,BOLIVIA:LATAM,ARGENTINA:LATAM,ECUADOR:LATAM,"
        "UAE:APAC,MALAYSIA:APAC,JAPAN:APAC,SINGAPORE:APAC,AUSTRALIA:APAC"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        # Origins are exact matches: localhost and 127.0.0.1 are different browser origins.
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def country_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for pair in self.country_georegion_mapping.split(","):
            parts = pair.strip().split(":")
            if len(parts) == 2:
                mapping[parts[0].strip()] = parts[1].strip()
        return mapping


settings = Settings()
