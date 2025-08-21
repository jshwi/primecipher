import os

PROVIDER = os.getenv("PROVIDER", "dexscreener").lower()
CHAIN_ID = os.getenv("CHAIN_ID", "solana").lower()

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# Survival & sanity thresholds
LIQ_SURVIVAL_THRESHOLD_USD = float(os.getenv("LIQ_SURVIVAL_THRESHOLD_USD", "1000"))
LIQ_MAX_USD = float(os.getenv("LIQ_MAX_USD", "250000000"))  # drop absurd outliers
VOL_MIN_USD = float(os.getenv("VOL_MIN_USD", "50"))         # ignore dust

# Which DEXes to accept on this chain
DEX_IDS = {d.strip().lower() for d in os.getenv("DEX_IDS", "raydium,orca,pump").split(",") if d.strip()}

# Directories
from pathlib import Path
DATA_DIR = os.getenv("DATA_DIR", str((Path(__file__).resolve().parents[2] / "data")))
SEED_DIR = os.getenv("SEED_DIR", str((Path(__file__).resolve().parents[2] / "seeds")))

