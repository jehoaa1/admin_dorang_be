from dataclasses import dataclass
import os
from dotenv import load_dotenv

# .env 파일을 읽어옵니다.
load_dotenv()
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HOST = os.environ.get("DB_HOST")
PORT = int(os.environ.get("DB_PORT"))
DBNAME = os.environ.get("DB_NAME")
USERNAME = os.environ.get("DB_USER")
PASSWORD = os.environ.get("DB_PASSWORD")

@dataclass
class Config:
    """
    기본 Configuration
    """
    BASE_DIR: str = base_dir
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = True
    DEBUG: bool = False
    TEST_MODE: bool = False
    DB_URL: str = os.environ.get("DB_URL", f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}")


@dataclass
class LocalConfig(Config):
    TRUSTED_HOSTS = ["*"]
    ALLOW_SITE = ["*"]
    DEBUG: bool = True


@dataclass
class ProdConfig(Config):
    TRUSTED_HOSTS = ["*"]
    ALLOW_SITE = ["*"]


@dataclass
class TestConfig(Config):
    DB_URL: str = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
    TRUSTED_HOSTS = ["*"]
    ALLOW_SITE = ["*"]
    TEST_MODE: bool = True


def conf():
    """
    환경 불러오기
    :return:
    """
    config = dict(prod=ProdConfig, local=LocalConfig, test=TestConfig)
    return config[os.environ.get("API_ENV", "local")]()


