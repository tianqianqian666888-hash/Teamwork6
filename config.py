import configparser
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.ini"
config = configparser.ConfigParser()

if CONFIG_FILE.exists():
    config.read(str(CONFIG_FILE), encoding='utf-8')