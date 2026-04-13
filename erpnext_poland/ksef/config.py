# core/config.py

import configparser
import os
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings
from frappe.utils import get_bench_path

config = configparser.ConfigParser()
ini_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(ini_path)

class KSeF2Settings(BaseModel):
  """Model dla sekcji [ksef2]"""
  cert_pfx: str
  cert_pass: str
  nip : str
  api_url : str


  @field_validator('cert_pfx')
  @classmethod
  def resolve_cert_path(cls, v: str) -> str:
    # ścieżka względna w stosunku do bench
    if not os.path.isabs(v):
      bench_path = get_bench_path()
      return os.path.join(bench_path, v)
    return v

# --- Główna klasa ustawień, która agreguje wszystkie sekcje ---
class Settings(BaseSettings):
  ksef2: KSeF2Settings

#def iniSettings():
#  my_settings=Settings(
#  ksef2 = KSeF2Settings(**config['ksef2']),
#  )
#  return my_settings


# --- Logika ładowania ustawień ---
settings = Settings(
  ksef2 = KSeF2Settings(**config['ksef2']),
)
