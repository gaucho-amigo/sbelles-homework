"""
Generate airport lookup CSV for OOH airport-to-state mapping.

Downloads the full OurAirports dataset from:
    https://davidmegginson.github.io/ourairports-data/airports.csv

Filters to the 20 IATA codes used in S'Belles OOH advertising data and
writes a slim lookup table with columns:
    iata_code, name, municipality, state, iso_country

State is derived from the iso_region field (e.g. "US-GA" -> "GA").

Usage:
    python -m src.reference_data.airports

Output:
    reference_data/airport_lookup.csv
"""

import csv
import io
import ssl
import urllib.error
import urllib.request
from pathlib import Path

OURAIRPORTS_URL = (
    "https://davidmegginson.github.io/ourairports-data/airports.csv"
)

TARGET_IATA_CODES = {
    "ATL", "BOS", "BWI", "CLT", "DEN", "DFW", "DTW", "IAH", "JFK", "LAS",
    "LAX", "LGA", "MCO", "MIA", "MSP", "ORD", "PHL", "PHX", "SEA", "SFO",
}

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "reference_data"
OUTPUT_FILE = OUTPUT_DIR / "airport_lookup.csv"


def _download_airports_csv() -> str:
    """Download the full OurAirports airports.csv and return as text."""
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(OURAIRPORTS_URL, context=ctx) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.URLError:
        # macOS Python may lack root certs; fall back to unverified for
        # this public, non-sensitive GitHub Pages download.
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(OURAIRPORTS_URL, context=ctx) as resp:
            return resp.read().decode("utf-8")


def build_lookup(raw_csv_text: str) -> list[dict]:
    """Filter raw OurAirports data to target IATA codes."""
    reader = csv.DictReader(io.StringIO(raw_csv_text))
    rows = []
    for row in reader:
        iata = row.get("iata_code", "").strip()
        if iata in TARGET_IATA_CODES:
            region = row.get("iso_region", "")
            state = region.split("-", 1)[1] if "-" in region else region
            rows.append({
                "iata_code": iata,
                "name": row.get("name", ""),
                "municipality": row.get("municipality", ""),
                "state": state,
                "iso_country": row.get("iso_country", ""),
            })
    rows.sort(key=lambda r: r["iata_code"])
    return rows


def main() -> None:
    print(f"Downloading airport data from {OURAIRPORTS_URL} ...")
    raw = _download_airports_csv()

    rows = build_lookup(raw)
    print(f"Matched {len(rows)} of {len(TARGET_IATA_CODES)} target airports")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["iata_code", "name", "municipality", "state", "iso_country"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
