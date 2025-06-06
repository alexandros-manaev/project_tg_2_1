"""Simple interface to query Open Food Facts for omega-3 information."""

from __future__ import annotations

import logging
import re
from typing import Optional

import requests

OMEGA3_KEYWORDS = [
    "лосось", "salmon", "скумбрия", "mackerel", "сельдь", "herring",
    "сардины", "sardines", "форель", "trout", "треска", "cod",
    "анчоус", "anchovy", "анчоусы", "anchovies", "икра", "caviar",
    "печень", "liver", "сига", "bluefish", "угорь", "eel",
    "устрицы", "oysters", "камбала", "flounder", "палтус", "halibut",
]


def is_omega3_product(product_name: str) -> bool:
    lower_name = product_name.lower()
    for keyword in OMEGA3_KEYWORDS:
        if keyword in lower_name:
            logging.debug("is_omega3_product('%s') -> True (keyword '%s')", product_name, keyword)
            return True
    logging.debug("is_omega3_product('%s') -> False", product_name)
    return False


def clean_product_name(product_name: str) -> str:
    name = re.sub(r"\s+", " ", product_name)
    name = re.sub(r"\(.*?\)", "", name)
    return name.strip()


def get_omega3_for_product(product_name: str, product_weight: float = 100.0) -> float:
    """Return omega-3 content in milligrams for a given product and weight."""
    query = clean_product_name(product_name)
    try:
        resp = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params={"search_terms": query, "search_simple": 1, "json": 1, "action": "process"},
            timeout=10,
        )
        data = resp.json()
        products = data.get("products", [])
        if not products:
            return 0.0
        nutriments = products[0].get("nutriments", {})
        omega3 = nutriments.get("omega-3-fat_100g") or nutriments.get("omega-3-fat")
        omega3_value = float(omega3) if omega3 is not None else 0.0
    except Exception as e:  # requests or JSON errors
        logging.error("OpenFoodFacts query failed for '%s': %s", product_name, e)
        return 0.0
    omega3_mg = omega3_value * 1000
    total = omega3_mg * product_weight / 100
    logging.debug(
        "Для '%s' (query: '%s') с массой %s г возвращено значение омега‑3: %.2f мг",
        product_name,
        query,
        product_weight,
        total,
    )
    return total

