import os
from pathlib import Path


def load_env_file(path=".env"):
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class Config:
    def __init__(self, api_key=None, cx=None):
        load_env_file()
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.cx = cx or os.environ.get("GOOGLE_CSE_ID")
        if not self.api_key:
            raise SystemExit(
                "Missing Google API key. Set GOOGLE_API_KEY in the environment, "
                "in a .env file, or pass --api-key."
            )
        if not self.cx:
            raise SystemExit(
                "Missing Programmable Search Engine ID (cx). Set GOOGLE_CSE_ID in "
                "the environment, in a .env file, or pass --cx."
            )
