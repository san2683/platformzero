# PlatformZero

**跑酷平台搭建器：将二维平台游戏的地图、动作接口与物理规则接入独立、无渲染的模拟环境，用于快速并行采样。** 从 Celeste 适配开始。

A headless 2D platformer simulation and environment builder for fast reinforcement-learning sampling, starting with Celeste adapters.

**Status: early development / documentation scaffold.** This repository currently contains the release plan, source-selection records and publication boundaries. It does **not yet contain an installable package or runnable Celeste simulator**. PlatformZero remains a working project name.

The intended workflow is:

```text
Supported game data (imported locally by the user)
        + explicit action and physics adapter
        → standalone headless environment
        → parallel rollouts, state restore and reproducible benchmarks
```

The original game is not required to render or run during headless sampling. Physics parity and native-game transfer must be measured for each supported adapter; approximation is not advertised as exact replication.

## What the project is intended to deliver

- A fast, headless platformer simulation backend for parallel sampling.
- Explicit game adapters, legal action/duration contracts and deterministic state capture/restore.
- A stable environment API for external training pipelines, including shared-policy PPO.
- Reproducible environment benchmarks and policy evaluations.
- User-local import of supported game data; an original synthetic example that needs no commercial game.

These are delivery targets, not a claim that every feature has already been extracted into this repository.

## Publication boundary

Do not distribute commercial game binaries, original maps, sprites, music, game DLLs, decompiled reference trees, private experiment bundles, checkpoints or credentials here. A local importer does not itself establish legal clearance for every code component.

The simulator is the central deliverable. A generic toy environment or a training wrapper alone must not be presented as a finished fast Celeste simulator.

See [release plan](docs/RELEASE_PLAN.md), [source provenance](provenance/UPSTREAM.md), [selection ledger](provenance/SOURCE_SELECTION.csv), and [name review](docs/NAME_REVIEW.md).

## Current contents and next steps

- Three research workspaces inventoried without remote mutation.
- Public/private boundaries and candidate source hashes recorded.
- No research files moved or deleted.
- This initial public scaffold contains documentation and a candidate source ledger, not simulator implementation files.
- Next: trace and extract the simulation backend and its explicit dependencies.
- Then: add a user-local map importer, authored synthetic levels, installation instructions and deterministic rollout/restore checks.
- Before a runnable release: publish a measured throughput benchmark and supported/approximate/unsupported mechanism table.
- Source provenance, runnable packaging and reproducibility acceptance remain open.

No blanket code license is assigned at this preparation stage. Third-party license notices must follow the files they cover.
