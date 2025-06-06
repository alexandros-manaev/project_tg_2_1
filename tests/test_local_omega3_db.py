import csv
import os
import tempfile
import unittest
from src.local_omega3_db import load_local_omega3_db

class LocalDbTest(unittest.TestCase):
    def test_load_local_db(self):
        with tempfile.NamedTemporaryFile('w+', newline='', encoding='utf-8-sig', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=["Description_RU", "Omega3 (g)"])
            writer.writeheader()
            writer.writerow({"Description_RU": "Горбуша", "Omega3 (g)": "1.0"})
            path = f.name
        data = load_local_omega3_db(path)
        os.remove(path)
        self.assertEqual(data[0]["Description_RU"], "Горбуша")

if __name__ == '__main__':
    unittest.main()

