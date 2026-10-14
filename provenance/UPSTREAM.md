# Source and asset provenance

## Shipped v0.1.0

Only the project's generic synthetic physics has been extracted. New package wrappers, state restoration, sampling/benchmark tools, tests and all three example maps were authored for PlatformZero. See `RELEASED_FILES.json` for exact hashes and extraction changes. No code from the Celeste-specific replica/native integration candidates below is distributed in this version. No real Celeste map importer is included.

## Developer-published Celeste source

- Repository: https://github.com/NoelFB/Celeste
- License: https://github.com/NoelFB/Celeste/blob/master/LICENSE
- Scope explanation: https://github.com/NoelFB/Celeste#source-code

The public repository uses MIT for the code it contains. This does not license the entire commercial game, commercial binaries, maps, textures or music. Preserve the applicable upstream copyright and permission notice with any covered code.

## Native integration

- Everest: https://github.com/EverestAPI/Everest

Review exact versions and copied files before packaging. Reference a user-installed game for building an adapter; do not bundle game DLLs or content.

## Current unresolved boundary

The research workspace includes decompiled reference files and compact physics/entity implementations. A simulator header describing developer-published Player.cs is not a file-by-file provenance audit. Some entity behavior also references native-game implementations; these portions require tracing or independent replacement before release.

No claim of a complete clean-room implementation or blanket MIT compatibility is made here. Local asset import avoids bundling assets but does not settle all questions about code provenance or terms.

## Required ledger

For each exported implementation record origin, upstream revision, modification summary, license/notice, dependencies and acceptance status. SOURCE_SELECTION.csv is an initial selection/hash ledger, not proof of copyright ownership.
