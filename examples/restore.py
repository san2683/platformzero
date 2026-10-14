"""Run after `pip install .`: restore mid-action and compare exact suffixes."""
import json

from platformzero import HeadlessEnv, load_example

original = HeadlessEnv(load_example("two_gaps"), seed=42)
original.reset()
for _ in range(4):
    original.step((2, 1, 0))
snapshot = json.loads(json.dumps(original.get_state()))
restored = HeadlessEnv()
restored.set_state(snapshot)
compared = 0
for _ in range(50):
    action = original.sample_action()
    assert action == restored.sample_action()
    assert original.step(action) == restored.step(action)
    assert original.get_state() == restored.get_state()
    compared += 1
    if original.world.status != "playing":
        break
print(json.dumps({"exact_suffix_decisions": compared, "status": original.world.status,
                  "snapshot_json_roundtrip": True}))
