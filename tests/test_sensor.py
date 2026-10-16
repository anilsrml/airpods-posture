import unittest

from posture.sensor import parse_gravity

# AirPods 4'ten yakalanan gerçek paketler (spike, 2026-10-16).
# Sıra numarası varint olduğu için uzunluk 80 ya da 81 bayt olabiliyor.
PKT_81 = bytes.fromhex("04000400170000001000450008800110013a3e08101a3a01f8f50657011c0000030083964d55150000000047a98a27d01aae00090037003e843e843e843c000400ecff42023d036a0050fd863ac1030000")
PKT_80_WARMUP = bytes.fromhex("040004001700000010004400080810013a3e08101a3a01a0a30e37001c000003004205950b1500000000000000000000000000000000621062106210000000000000000000000000f09f2c3601000000")
PKT_80 = PKT_80_WARMUP[:66] + bytes.fromhex("08025f03ab00") + PKT_80_WARMUP[72:]


class ParseGravityTest(unittest.TestCase):
    def test_reads_gravity_vector_from_81_byte_packet(self):
        self.assertEqual(parse_gravity(PKT_81), (578, 829, 106))

    def test_reads_gravity_vector_from_80_byte_packet(self):
        self.assertEqual(parse_gravity(PKT_80), (520, 863, 171))

    def test_warmup_packet_with_zero_gravity_is_ignored(self):
        self.assertIsNone(parse_gravity(PKT_80_WARMUP))

    def test_other_packets_are_ignored(self):
        self.assertIsNone(parse_gravity(bytes.fromhex("04000400090018000000000000")))
        self.assertIsNone(parse_gravity(PKT_81[:40]))


if __name__ == "__main__":
    unittest.main()
