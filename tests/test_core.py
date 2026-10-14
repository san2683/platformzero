import dataclasses
import json
import math
import unittest

from platformzero import Action, DT, Level, Rect, Rules, World, example_names, load_example


class PhysicsTests(unittest.TestCase):
    def world(self, **rules):
        return World(dataclasses.replace(load_example("runway"), rules=Rules(**rules)))

    def test_packaged_original_levels_are_valid(self):
        for name in example_names():
            level = load_example(name)
            self.assertEqual(level.name, name)
            world = World(level)
            self.assertTrue(world.grounded)
            self.assertEqual(world.frames, 0)

    def test_noop_stays_on_floor(self):
        w = self.world()
        for _ in range(200):
            w.tick(Action())
        self.assertEqual((w.x, w.y), w.level.spawn)
        self.assertTrue(w.grounded)
        self.assertEqual(w.frames, 200)

    def test_right_runner_reaches_goal(self):
        w = self.world()
        while w.status == "playing":
            w.tick(Action(move=1))
        self.assertEqual(w.status, "success")
        self.assertLess(w.frames, 300)
        before = w.get_state()
        self.assertEqual(w.tick(Action(move=1)), 0)
        self.assertEqual(w.get_state(), before)

    def test_jump_hold_is_an_edge_not_auto_rejump(self):
        w = self.world()
        w.tick(Action(jump=True))
        self.assertLess(w.y, w.level.spawn[1])
        for _ in range(90):
            w.tick(Action(jump=True))
        self.assertTrue(w.grounded)
        self.assertEqual(w.y, w.level.spawn[1])
        w.tick(Action()); w.tick(Action(jump=True))
        self.assertLess(w.y, w.level.spawn[1])

    def test_release_shortens_only_jump_ascent(self):
        held, cut = self.world(), self.world()
        for _ in range(4):
            held.tick(Action(jump=True)); cut.tick(Action(jump=True))
        held.tick(Action(jump=True)); cut.tick(Action())
        self.assertGreater(cut.vy, held.vy)
        self.assertFalse(cut.jump_active)

    def test_double_jump_requires_release(self):
        w = self.world(jumps=2)
        w.tick(Action(jump=True))
        for _ in range(5):
            w.tick(Action(jump=True))
        self.assertEqual(w.jumps_left, 1)
        w.tick(Action()); w.tick(Action(jump=True))
        self.assertEqual(w.jumps_left, 0)
        self.assertLess(w.vy, -9)

    def test_disabled_dash_is_noop(self):
        a, b = self.world(dash=False), self.world(dash=False)
        for _ in range(30):
            a.tick(Action(move=1, dash=1)); b.tick(Action(move=1))
            self.assertEqual((a.x,a.y,a.vx,a.vy),(b.x,b.y,b.vx,b.vy))

    def test_horizontal_dash_does_not_tunnel_thin_wall(self):
        level = load_example("runway")
        level = dataclasses.replace(level, platforms=level.platforms + (Rect(3,6,.02,2),))
        w = World(level)
        for _ in range(20):
            w.tick(Action(dash=1))
        self.assertLessEqual(w.x + w.player_w, 3 + 1e-9)
        self.assertEqual(w.status, "playing")

    def test_thin_hazard_kills_dashing_player(self):
        w = World(dataclasses.replace(load_example("runway"), hazards=(Rect(2.5,7.2,.02,.8),)))
        for _ in range(20):
            w.tick(Action(dash=1))
            if w.status != "playing":
                break
        self.assertEqual(w.status, "dead")
        self.assertEqual(w.last_terms["death"], -2)

    def test_timeout_is_exact(self):
        w = World(load_example("runway"), max_frames=3)
        for _ in range(3):
            w.tick(Action())
        self.assertEqual((w.frames,w.status), (3,"timeout"))

    def test_invalid_rules_and_actions_fail(self):
        for kwargs in ({"gravity":float("nan")},{"speed":False},{"jumps":3},{"dash":1}):
            with self.assertRaises(ValueError):
                Rules(**kwargs)
        for kwargs in ({"move":True},{"move":2},{"jump":1},{"dash":9},{"dash":1.5}):
            with self.assertRaises(ValueError):
                Action(**kwargs)
        with self.assertRaises(ValueError):
            Rect(0,0,0,1)

    def test_state_captures_mid_jump_and_dash(self):
        for action in (Action(move=1,jump=True), Action(dash=2)):
            w = self.world()
            for _ in range(3):
                w.tick(action)
            state = json.loads(json.dumps(w.get_state(), allow_nan=False))
            clone = World.from_state(state)
            self.assertEqual(clone.get_state(), w.get_state())
            for following in [action]*5 + [Action()]*5 + [Action(move=-1,jump=True)]*10:
                self.assertEqual(w.tick(following), clone.tick(following))
                self.assertEqual(w.get_state(), clone.get_state())

    def test_snapshot_is_detached(self):
        w = self.world(); state=w.get_state()
        state["dynamic"]["last_terms"]["bad"]=1
        state["level"]["rules"]["speed"]=1
        self.assertEqual(w.level.rules.speed,6)
        self.assertNotIn("bad",w.last_terms)

    def test_missing_button_history_and_bad_fingerprint_rejected(self):
        for mutation in ("missing", "fingerprint", "nan", "version", "button"):
            w=self.world(); w.tick(Action(jump=True)); s=w.get_state()
            if mutation=="missing": del s["dynamic"]["jump_held"]
            if mutation=="fingerprint": s["level"]["rules"]["speed"]=7
            if mutation=="nan": s["dynamic"]["vy"]=math.nan
            if mutation=="version": s["schema"]=999
            if mutation=="button": s["dynamic"]["jump_held"]=False
            with self.assertRaises(ValueError, msg=mutation):
                World.from_state(s)

    def test_dt_is_fixed_sixtieth(self):
        self.assertEqual(DT,1/60)

    def test_authored_gap_and_hazard_maps_have_valid_completion_paths(self):
        # Known example trajectories test geometry, not learned Bot capability.
        for name in ("two_gaps", "steps_and_spikes"):
            w=World(load_example(name));jump=False
            for _ in range(1000):
                if w.grounded:
                    jump=(5.5<w.x<7 or 14.5<w.x<16) if name=="two_gaps" else (5.5<w.x<7 or 13.5<w.x<15 or 19<w.x<23)
                elif name=="steps_and_spikes" and w.x>23.1 and w.jumps_left>0:
                    jump=not jump  # release then use the second jump over the final gap
                w.tick(Action(move=1 if w.x<w.level.goal.x else 0,jump=jump))
                if w.status!="playing":break
            self.assertEqual(w.status,"success",name)

    def test_progress_reward_and_death_state_survive_restore(self):
        w=self.world()
        for _ in range(20):w.tick(Action(move=1))
        for _ in range(10):w.tick(Action(move=-1))
        clone=World.from_state(json.loads(json.dumps(w.get_state())))
        for _ in range(10):
            self.assertEqual(w.tick(Action(move=1)),clone.tick(Action(move=1)))
            self.assertEqual(w.last_terms["progress"],0)
        dead=World(dataclasses.replace(load_example("runway"),hazards=(Rect(2.5,7.2,.02,.8),)))
        while dead.status=="playing":dead.tick(Action(move=1))
        self.assertEqual(dead.status,"dead")
        restored=World.from_state(json.loads(json.dumps(dead.get_state())))
        before=restored.get_state();self.assertEqual(restored.tick(Action()),0)
        self.assertEqual(before,restored.get_state())


if __name__ == "__main__":
    unittest.main()
