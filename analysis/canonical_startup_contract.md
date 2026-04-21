# Canonical Startup Contract

## Canonical entrypoint
- Primary runtime entrypoint: `jarvis_autonomous.py`

## Secondary entrypoints (legacy/dev)
- `jarvis_brain.py` - internal orchestration component runner
- `unified_launcher.py` - legacy/experimental launcher
- `main.py` / `main_old.py` - legacy compatibility scripts

## Policy
1. Production startup must invoke `jarvis_autonomous.py`.
2. Legacy entrypoints remain for compatibility until Wave B consolidation complete.
3. New automation scripts must call canonical entrypoint or document deviation.

## Environment contract (minimum)
- Required: `JWT_SECRET`
- Recommended: `GROQ_API_KEY`, `REDIS_HOST`, `REDIS_PORT`, `GRPC_PORT`, `WHATSAPP_PORT`

## Verification
- `python -c "import jarvis_autonomous"` succeeds
- `pytest -c pytest.smoke.ini -q tests/test_system_validation.py` passes
