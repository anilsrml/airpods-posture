import math
import unittest

from durus.engine import PostureEngine, State, pitch_from_gravity

UPRIGHT_PITCH = 49.0


def gravity(pitch_deg):
    """Verilen mutlak öne eğim açısına karşılık gelen yerçekimi vektörü."""
    r = math.radians(pitch_deg)
    return (1024 * math.cos(r), 1024 * math.sin(r), 0)


def feed(engine, t_from, t_to, pitch_deg, hz=25):
    """[t_from, t_to) aralığında sabit açıyla örnek gönderir; bildirim sayısını döndürür."""
    notes, n = 0, round((t_to - t_from) * hz)
    for i in range(n):
        notes += engine.update(t_from + i / hz, gravity(pitch_deg))
    return notes


def calibrated_engine():
    e = PostureEngine()
    e.connected(0.0)
    feed(e, 0, 3, UPRIGHT_PITCH)
    return e


class PitchFromGravityTest(unittest.TestCase):
    def test_forward_tilt_is_angle_in_xy_plane(self):
        self.assertAlmostEqual(pitch_from_gravity((1024, 0, 0)), 0.0)
        self.assertAlmostEqual(pitch_from_gravity((724, 724, 0)), 45.0)

    def test_other_earbud_mirrors_x_axis(self):
        self.assertAlmostEqual(pitch_from_gravity((-724, 724, 0)), 45.0)


class EngineTest(unittest.TestCase):
    def test_starts_disconnected(self):
        self.assertEqual(PostureEngine().state, State.DISCONNECTED)

    def test_calibrates_during_first_seconds_after_connect(self):
        e = PostureEngine()
        e.connected(0.0)
        feed(e, 0, 2, UPRIGHT_PITCH)
        self.assertEqual(e.state, State.CALIBRATING)

    def test_upright_after_calibration_with_zero_pitch(self):
        e = calibrated_engine()
        feed(e, 3, 4, UPRIGHT_PITCH)
        self.assertEqual(e.state, State.UPRIGHT)
        self.assertAlmostEqual(e.pitch, 0.0, places=3)

    def test_leaning_when_forward_past_threshold_briefly(self):
        e = calibrated_engine()
        feed(e, 3, 13, UPRIGHT_PITCH + 20)
        self.assertEqual(e.state, State.LEANING)
        self.assertAlmostEqual(e.pitch, 20.0, places=3)

    def test_slouched_when_leaning_lasts_past_slouch_time(self):
        e = calibrated_engine()
        feed(e, 3, 24, UPRIGHT_PITCH + 20)
        self.assertEqual(e.state, State.SLOUCHED)

    def test_sitting_up_resets_slouch_timer(self):
        e = calibrated_engine()
        feed(e, 3, 18, UPRIGHT_PITCH + 20)
        feed(e, 18, 19, UPRIGHT_PITCH)
        self.assertEqual(e.state, State.UPRIGHT)
        feed(e, 19, 34, UPRIGHT_PITCH + 20)
        self.assertEqual(e.state, State.LEANING)

    def test_leaning_back_counts_as_upright(self):
        e = calibrated_engine()
        feed(e, 3, 30, UPRIGHT_PITCH - 25)
        self.assertEqual(e.state, State.UPRIGHT)

    def test_notifies_once_after_slouching_for_notify_time(self):
        e = calibrated_engine()
        # 3 sn + 20 sn eğik = kambur (t=23); +30 sn = bildirim (t=53)
        self.assertEqual(feed(e, 3, 52, UPRIGHT_PITCH + 20), 0)
        self.assertEqual(feed(e, 52, 120, UPRIGHT_PITCH + 20), 1)

    def test_notifies_again_after_sitting_up_and_slouching_again(self):
        e = calibrated_engine()
        feed(e, 3, 60, UPRIGHT_PITCH + 20)
        feed(e, 60, 61, UPRIGHT_PITCH)
        self.assertEqual(feed(e, 61, 120, UPRIGHT_PITCH + 20), 1)

    def test_paused_ignores_samples_and_never_notifies(self):
        e = calibrated_engine()
        e.pause()
        self.assertEqual(feed(e, 3, 120, UPRIGHT_PITCH + 20), 0)
        self.assertEqual(e.state, State.PAUSED)

    def test_resume_starts_slouch_timer_fresh(self):
        e = calibrated_engine()
        feed(e, 3, 18, UPRIGHT_PITCH + 20)
        e.pause()
        feed(e, 18, 30, UPRIGHT_PITCH + 20)
        e.resume()
        feed(e, 30, 40, UPRIGHT_PITCH + 20)
        self.assertEqual(e.state, State.LEANING)

    def test_recalibrate_takes_new_zero_from_current_posture(self):
        e = calibrated_engine()
        e.recalibrate(3.0)
        feed(e, 3, 7, UPRIGHT_PITCH + 20)
        self.assertEqual(e.state, State.UPRIGHT)
        self.assertAlmostEqual(e.pitch, 0.0, places=3)

    def test_disconnect_clears_pitch(self):
        e = calibrated_engine()
        e.disconnected()
        self.assertEqual(e.state, State.DISCONNECTED)
        self.assertIsNone(e.pitch)

    def test_reconnect_needs_new_zero(self):
        e = calibrated_engine()
        e.disconnected()
        e.connected(10.0)
        feed(e, 10, 14, UPRIGHT_PITCH + 8)
        self.assertAlmostEqual(e.pitch, 0.0, places=3)

    def test_resume_while_disconnected_stays_disconnected(self):
        e = PostureEngine()
        e.pause()
        e.resume()
        self.assertEqual(e.state, State.DISCONNECTED)

    def test_first_sample_after_zero_window_becomes_zero(self):
        e = PostureEngine()
        e.connected(0.0)
        feed(e, 5, 6, UPRIGHT_PITCH)
        self.assertEqual(e.state, State.UPRIGHT)
        self.assertAlmostEqual(e.pitch, 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
