# Wave B Bridge Plan (Activated)

## Scope
1. Entrypoint unification prep
2. Config contract centralization prep
3. Capability registry baseline

## Immediate implementation tasks

### B1 - Entrypoint inventory tagging
- Add explicit header comments to legacy entrypoints indicating non-canonical status.
- Files: `jarvis_brain.py`, `unified_launcher.py`, `main.py`, `main_old.py`.

### B2 - Config contract centralization prep
- Introduce one config module contract map in `core/config.py` with required/optional env keys and validator function.
- Wire `jarvis_autonomous.py` to use validator warning output.

### B3 - Capability registry baseline
- Create `analysis/capability_registry_seed.md` mapping active core modules to capability classes.

## Exit gates for Wave B
- Canonical vs legacy entrypoint status explicitly documented in code/docs.
- Single config contract source present and referenced by canonical entrypoint.
- Capability registry seed produced for top-level core modules.
