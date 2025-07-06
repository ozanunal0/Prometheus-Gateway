import os
import pathlib
import yaml
from pydantic import BaseModel


class ProviderConfig(BaseModel):
    name: str
    api_key_env: str
    models: list[str]

    @property
    def api_key(self) -> str:
        """Retrieves the API key from the environment variable."""
        key = os.getenv(self.api_key_env)
        if not key:
            raise ValueError(f"Environment variable {self.api_key_env} not set.")
        return key


class Config(BaseModel):
    providers: list[ProviderConfig]


def load_config(config_path: str = "config.yaml") -> Config:
    """Loads, parses, and validates the YAML configuration file."""
    path = pathlib.Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    with open(path, "r") as f:
        config_data = yaml.safe_load(f)
    
    return Config.model_validate(config_data)


# Singleton config instance
config = load_config() 