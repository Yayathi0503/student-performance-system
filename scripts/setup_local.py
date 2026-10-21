"""Create local secrets once without printing them or overwriting an existing .env."""

import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
target = root / ".env"
if target.exists():
    print("Existing .env preserved.")
else:
    with target.open("x", encoding="utf-8") as output:
        output.write(
            f"JWT_SECRET={secrets.token_hex(32)}\nMYSQL_PASSWORD={secrets.token_hex(24)}\nMYSQL_ROOT_PASSWORD={secrets.token_hex(24)}\n"
        )
    print("Created .env with random local secrets. Keep this file private.")
