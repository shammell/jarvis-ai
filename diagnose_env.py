import os
from dotenv import load_dotenv

load_dotenv()

keys_to_check = [
    "JWT_SECRET",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "ADMIN_PASSWORD"
]

print("--- ENV DIAGNOSTICS ---")
for key in keys_to_check:
    val = os.getenv(key)
    if val:
        print(f"[OK] {key} is set (length: {len(val)})")
    else:
        print(f"[MISSING] {key} is NOT set")
print("--- END ---")
