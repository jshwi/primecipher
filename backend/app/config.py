import os

PROVIDER = os.getenv("PROVIDER", "dexscreener").lower()
CHAIN_ID = os.getenv("CHAIN_ID", "solana")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
LIQ_SURVIVAL_THRESHOLD_USD = float(os.getenv("LIQ_SURVIVAL_THRESHOLD_USD", "1000"))
DATA_DIR = os.getenv("DATA_DIR", str((__import__('pathlib').Path(__file__).resolve().parents[2] / 'data')))
SEED_DIR = os.getenv("SEED_DIR", str((__import__('pathlib').Path(__file__).resolve().parents[2] / 'seeds')))
