import os

def autonomy_enabled() -> bool:
    val = os.getenv("AUTONOMOUS_MODE", "false").lower()
    return val in ("1", "true", "yes", "on")

def require_autonomy(action_name: str) -> None:
    if not autonomy_enabled():
        raise RuntimeError(
            f"Autonomous mode is DISABLED. Blocked action: '{action_name}'. "
            f"Set AUTONOMOUS_MODE=true in .env to enable."
        )