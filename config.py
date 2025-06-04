import logging
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.RABBITMQ_HOSTNAME = os.getenv('RABBITMQ_HOSTNAME', '')
        self.RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
        self.RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
        self.AGENT_IP = os.getenv('AGENT_IP', '')
        self.EXCHANGE_NAME = os.getenv('EXCHANGE_NAME', 'nftables')


settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
