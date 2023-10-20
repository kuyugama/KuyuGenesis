from pathlib import Path

from configparser import ConfigParser

parser = ConfigParser()
parser.read("./KuyuGenesis.conf")

proxy = parser["Main"]

accounts_count = proxy.getint("accounts_count")
sessions_root = Path(proxy.get("sessions_root"))

version = "1.1.3"
name = proxy.get("name")

api_id = proxy.get("api_id")
api_hash = proxy.get("api_hash")

auto_install_dependencies = parser.getboolean("Addons", "auto_install_dependencies")
addons_root = Path(parser.get("Addons", "root"))
