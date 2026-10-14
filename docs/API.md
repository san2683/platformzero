# v0.1.0 API and physics contract

## Supported simulation

`World(level, max_frames=1800).tick(Action(...))` advances exactly one 1/60-second physical frame while playing. It returns the scalar reward; ticks after a terminal state return zero without changing state. `HeadlessEnv.step()` repeats an action for 1..8 frames, stopping immediately on a terminal state. It returns `(observation, reward, terminated, truncated, info)`.

Positions use metres with x right and y down. Player size is 0.55 × 0.8 m. Default gravity is 24 m/s², horizontal speed 6 m/s, jump impulse 10 m/s, dash speed 16 m/s for nine frames. Horizontal velocity changes immediately; this is **not an acceleration/friction model**. Solids are static axis-aligned rectangles. Substeps bound displacement to 0.1 m before collision/hazard checks. No render path is called or required.

Jump uses a button rising edge and requires release before another jump. Grounding restores jump count; walking off a ledge consumes the ground jump, without coyote time. Only jump-origin upward motion is shortened on release. Dash also uses a rising edge; landing after airborne motion restores enabled dash. This is a simplified synthetic rule set, not a Celeste compatibility specification.

## Actions

`Action(move, jump, dash)` uses move -1/0/+1 and boolean jump. List/tuple indices are `[move + 1, int(jump), dash]`, factors `[3,2,9]`. NumPy/Gym are not dependencies; convert NumPy arrays with `.tolist()`.

| Dash index | Direction |
|---:|---|
| 0 | Released / no dash |
| 1 | Right |
| 2 | Up-right |
| 3 | Up |
| 4 | Up-left |
| 5 | Left |
| 6 | Down-left |
| 7 | Down |
| 8 | Down-right |

Diagonals are normalized. Under `Rules(dash=False)`, dash has no effect although button history is recorded. Invalid actions are rejected before any frame advances. No action-duration head or wall-climb control is present.

## Observation, reward and terminal state

`platformzero-state-v1` is a plain dictionary: position, velocity, grounded, jumps_left, dash_ready, dash_frames, jump_held, dash_held, frames_remaining. It is engine telemetry, **not pixels or a perception/generalization benchmark**. No map tensor or renderer cost is hidden in throughput. Clients can inspect `Level` and construct their own encoding.

Reward per frame: new furthest-right progress divided by level width, time -0.001, success +10, death -2. This shaping serves synthetic examples; it is not the new shared-memory research policy's contract. Reward terms and return are captured. Progress cannot be farmed by moving back and forth.

Goal overlap produces `success`; hazard overlap or falling below the level produces `dead`; frame limit produces `timeout`. Death/success set `terminated=True`, time limit sets `truncated=True`. Death precedes goal. `physics_frames_delta` may be less than frame_skip. The API never silently auto-resets or invents frames.

## Maps

The three JSON files under `src/platformzero/maps/` were authored for this release; no imported game geometry is present. For your own authored map:

```json
{"schema":"platformzero-map-v1","authorship":"Your author credit","level":{
  "name":"example","width":24.0,"height":12.0,
  "platforms":[{"x":0.0,"y":8.0,"w":24.0,"h":4.0}],"hazards":[],
  "spawn":[1.0,7.2],"goal":{"x":22.0,"y":6.7,"w":0.75,"h":1.3},
  "rules":{}
}}
```

`load_level(path)` accepts this JSON schema up to 1 MB, not `.bin`/native-game formats. Geometry must be inside bounds; spawn cannot overlap solids/hazards. `Level`/`Rect`/`Rules` are immutable.

## Complete environment state

`get_state()` returns detached JSON-safe data; `set_state()` validates before atomic replacement:

- schema and engine version;
- embedded immutable level/rules and canonical SHA-256 fingerprint;
- position/velocity, grounded/resources, dash counter;
- held jump/dash, jump-active flag and last action;
- frame limit/count, terminal state, furthest progress, reward terms and return;
- frame_skip and Python `Random` action-sampler state.

Fingerprint mismatch, missing held-button fields, incompatible versions, invalid values and malformed RNG reject the restore. Snapshots are data, not executable pickle. This is not a training checkpoint: optimizer, policy RNG/model memory and process identity belong to the caller.

Tests compare exact continuations after JSON round-trips mid-jump/mid-dash, sampler restoration, terminal restoration and receiver reconfiguration, plus atomic rejection. Cross-runtime bitwise compatibility needs separate evidence.
