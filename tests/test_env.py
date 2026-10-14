import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from platformzero import Action, HeadlessEnv, load_example, load_level
from platformzero.benchmark import run_benchmark


class EnvironmentTests(unittest.TestCase):
    def env(self, **kwargs):
        e=HeadlessEnv(load_example("runway"), **kwargs);e.reset();return e

    def test_five_value_api_and_actual_short_duration(self):
        e=self.env(max_frames=3,frame_skip=4)
        obs,reward,terminated,truncated,info=e.step((1,0,0))
        self.assertFalse(terminated);self.assertTrue(truncated)
        self.assertEqual(info["physics_frames_delta"],3)
        self.assertEqual(obs["frames_remaining"],0)
        self.assertAlmostEqual(reward,-.003)
        with self.assertRaises(RuntimeError):e.step((1,0,0))

    def test_terminal_success_not_timeout(self):
        e=self.env()
        while e.world.status=="playing": result=e.step((2,0,0))
        self.assertTrue(result[2]);self.assertFalse(result[3])
        self.assertTrue(result[4]["is_success"])

    def test_invalid_action_no_mutation(self):
        e=self.env(); before=e.get_state()
        for action in ([3,0,0],[0,1,9],[0,True,0],[-1,0,0],[0,0],None):
            with self.assertRaises(ValueError):e.step(action)
            self.assertEqual(e.get_state(),before)

    def test_json_snapshot_restores_sampler_and_exact_continuation(self):
        e=self.env(seed=17)
        for _ in range(5):e.step((2,1,0))
        saved=json.loads(json.dumps(e.get_state()))
        clone=HeadlessEnv(load_example("steps_and_spikes"),frame_skip=1,seed=99)
        clone.set_state(saved)
        for _ in range(100):
            action=e.sample_action();self.assertEqual(action,clone.sample_action())
            self.assertEqual(e.step(action),clone.step(action))
            self.assertEqual(e.get_state(),clone.get_state())
            if e.world.status!="playing":
                self.assertEqual(e.reset(),clone.reset())

    def test_rejected_restore_is_atomic(self):
        e=self.env(seed=7);e.step((2,1,0));before=e.get_state()
        for bad_rng in ([3],None,[3,[],None]):
            bad=copy.deepcopy(before);bad["sampler_rng"]=bad_rng
            with self.assertRaises(ValueError):e.set_state(bad)
            self.assertEqual(e.get_state(),before)
        bad=copy.deepcopy(before);bad["world"]["dynamic"]["frames"]=100000000
        with self.assertRaises(ValueError):e.set_state(bad)
        self.assertEqual(e.get_state(),before)

    def test_terminal_snapshot_restores_and_reset_replays(self):
        e=self.env(max_frames=5)
        e.step(Action());e.step(Action())
        c=HeadlessEnv();c.set_state(json.loads(json.dumps(e.get_state())))
        self.assertEqual(c.world.status,"timeout")
        with self.assertRaises(RuntimeError):c.step((1,0,0))
        self.assertEqual(c.reset(),e.reset())

    def test_seed_reproduces_action_sampler(self):
        a=self.env(seed=5);b=self.env(seed=5)
        self.assertEqual([a.sample_action() for _ in range(50)],[b.sample_action() for _ in range(50)])
        a.reset(seed=5);b.reset(seed=5)
        self.assertEqual(a.sample_action(),b.sample_action())

    def test_load_authored_json_and_reject_native_file(self):
        level=load_example("two_gaps")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"map.json"
            p.write_text(json.dumps({"schema":"platformzero-map-v1","authorship":"User-authored synthetic test", "level":level.to_dict()}),encoding="utf-8")
            self.assertEqual(load_level(p),level)
            p=Path(d)/"map.bin";p.write_bytes(b"native data")
            with self.assertRaises(ValueError):load_level(p)

    def test_benchmark_counts_actual_frames_without_renderer(self):
        p=run_benchmark(mode="physics",steps=200,warmup=10,repeats=1)
        self.assertEqual(p["trials"][0]["actual_physics_frames"],200)
        self.assertEqual(p["trials"][0]["actual_decisions"],0)
        q=run_benchmark(mode="env",steps=100,warmup=10,repeats=1)
        self.assertEqual(q["trials"][0]["actual_decisions"],100)
        self.assertLessEqual(q["trials"][0]["actual_physics_frames"],400)
        self.assertGreater(q["median_physics_fps_end_to_end"],0)
        self.assertFalse(any(m in sys.modules for m in ("pygame","tkinter","gymnasium","torch")))

    def test_installed_module_cli(self):
        p=subprocess.run([sys.executable,"-m","platformzero","sample","--level","runway",
                          "--policy","right","--episodes","2"],capture_output=True,text=True,check=True)
        result=json.loads(p.stdout)
        self.assertEqual(result["actual"]["success"],2)
        self.assertFalse(result["rendering"])

    def test_spawned_benchmark_has_exact_job_counts(self):
        p=subprocess.run([sys.executable,"-m","platformzero","benchmark","--mode","physics",
                          "--workers","2","--steps","100","--warmup","10","--repeats","1"],
                         capture_output=True,text=True,check=True)
        result=json.loads(p.stdout)
        self.assertEqual(result["trials"][0]["actual_physics_frames"],200)
        self.assertEqual(len(result["trials"][0]["workers"]),2)

    def test_invalid_benchmark_configuration_rejected_before_sampling(self):
        for config in ({"workers":0},{"steps":0},{"repeats":0},{"warmup":-1},{"mode":"render"}):
            with self.assertRaises(ValueError):run_benchmark(**config)


if __name__ == "__main__":
    unittest.main()
