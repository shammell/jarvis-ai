# Refactor Backlog

## P0
1. Fix `jarvis_autonomous.py` log-path bootstrap when `logs/` missing.
2. Define canonical startup entrypoint and deprecate shadow launchers.
3. Unify env/config contract (`JWT_SECRET` critical gate).
4. Split smoke-test profile from strict coverage profile.

## P1
1. Consolidate orchestration interfaces and remove temp variants.
2. Add capability registry for optional advanced modules in `core/`.
3. Normalize gRPC structure (`grpc_service` vs `grpc`).

## P2
1. Artifact hygiene for benchmark dumps.
2. CI orphan scanner + ownership metadata.
