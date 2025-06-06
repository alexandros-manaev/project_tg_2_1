import unittest
from src.fatsecret_api import parse_weight
import src.config as config

class ParseWeightTest(unittest.TestCase):
    def test_parse_weight_grams(self):
        self.assertEqual(parse_weight("100 г"), 100)

    def test_parse_weight_spoons(self):
        self.assertEqual(parse_weight("2 ложки"), 2 * config.TABLESPOON_GRAMS)

if __name__ == '__main__':
    unittest.main()

