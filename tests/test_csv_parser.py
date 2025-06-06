import csv
import os
import tempfile
import unittest
from src.csv_parser import extract_products_from_csv

class CsvParserTest(unittest.TestCase):
    def test_extract_products_basic(self):
        with tempfile.NamedTemporaryFile('w+', newline='', encoding='utf-8', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Белк( г)"])
            writer.writerow(["Яблоко", "0.3"])
            writer.writerow(["50 г"])
            path = f.name
        products = extract_products_from_csv(path)
        os.remove(path)
        self.assertEqual(products, [("Яблоко", "50 г", "0.3")])

if __name__ == '__main__':
    unittest.main()

