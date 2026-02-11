"""
Schema Design Investigation — Pre-schema profiling for S'Belles take-home.

Analyzes DMA standardization, state standardization, airport-to-geography mapping,
campaign linkage across paid social and web analytics, and podcast geography signals.

Outputs: docs/schema_design_notes.md
Run:     python -m src.exploration.schema_design_investigation
"""

import csv
import os
import re
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data")

PAID_SOCIAL_FILES = [
    "sBelles_paid_instagram_part1.csv",
    "sBelles_paid_instagram_part2.csv",
    "sBelles_paid_instagram_part3_schema_drift.csv",
    "sBelles_paid_pinterest_part1_schema_drift.csv",
    "sBelles_paid_pinterest_part2.csv",
    "sBelles_paid_pinterest_part3.csv",
    "sBelles_paid_tiktok_part1.csv",
    "sBelles_paid_tiktok_part2_schema_drift.csv",
    "sBelles_paid_tiktok_part3.csv",
]

WEB_FILES = [
    "sBelles_web_traffic_2023_Q1_Q2.csv",
    "sBelles_web_traffic_2023_Q3_Q4.csv",
    "sBelles_web_traffic_2024_Q1.csv",
    "sBelles_web_traffic_2024_Q2.csv",
]

TXN_FILES = [
    "sBelles_transactions_2023_Q1_Q2.csv",
    "sBelles_transactions_2023_Q3_Q4.csv",
    "sBelles_transactions_2024_Q1_Q2.csv",
]

OOH_FILE = "sBelles_ooh_airport_weekly.csv"

PODCAST_FILES = [
    "sBelles_podcast_mentions_2023_2024_part1.csv",
    "sBelles_podcast_mentions_2023_2024_part2.csv",
]

STREAM_GROUPS = {
    "paid_social": PAID_SOCIAL_FILES,
    "web_traffic": WEB_FILES,
    "transactions": TXN_FILES,
}


def read_csv(filename):
    path = os.path.join(DATA, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# -- Geographic reference terms for podcast analysis --
US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
    "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
    "Washington", "West Virginia", "Wisconsin", "Wyoming",
]
STATE_ABBREVS = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY",
]
CITIES = [
    "Atlanta", "ATL", "Nashville", "Charlotte", "Dallas", "Houston", "Miami",
    "Tampa", "Raleigh", "Savannah", "Charleston", "Memphis", "Birmingham",
    "Jacksonville", "New Orleans", "Austin", "San Antonio", "Richmond",
    "Louisville", "Knoxville", "Chattanooga", "Greenville", "Columbia", "Macon",
    "Augusta", "Athens",
]
REGIONAL = [
    "Southern", "Peach State", "Dixie", "Deep South", "Magnolia", "Gulf Coast",
    "Low Country", "Lowcountry", "Bible Belt", "Sun Belt", "Sunbelt",
]


def analyze_dma_standardization():
    """Section 1: DMA standardization across streams."""
    print("=" * 80)
    print("SECTION 1: DMA STANDARDIZATION ANALYSIS")
    print("=" * 80)

    dma_by_file = {}
    all_dma_values = set()

    for f in PAID_SOCIAL_FILES + WEB_FILES + TXN_FILES:
        rows = read_csv(f)
        vals = {r.get("dma_name", "") for r in rows if r.get("dma_name")}
        dma_by_file[f] = vals
        all_dma_values.update(vals)

    dma_by_stream = {}
    for stream, files in STREAM_GROUPS.items():
        combined = set()
        for f in files:
            combined.update(dma_by_file[f])
        dma_by_stream[stream] = combined

    print(f"\nTotal unique DMA values across all files: {len(all_dma_values)}")
    for stream, vals in dma_by_stream.items():
        print(f"  {stream}: {len(vals)} unique DMAs")

    print("\nAll unique DMA values (sorted):")
    for v in sorted(all_dma_values):
        sources = []
        for stream, files in STREAM_GROUPS.items():
            for f in files:
                if v in dma_by_file[f]:
                    sources.append(stream)
                    break
        print(f"  '{v}' -> found in: {', '.join(sorted(set(sources)))}")

    # Near-match detection
    normalized = defaultdict(list)
    for v in all_dma_values:
        key = v.lower().strip().replace("  ", " ")
        normalized[key].append(v)

    near_matches = {k: v for k, v in normalized.items() if len(v) > 1}
    if near_matches:
        print("\n*** NEAR-MATCH DMA VALUES (potential duplicates) ***")
        for norm, variants in near_matches.items():
            print(f"  Normalized '{norm}': {variants}")
    else:
        print("\nNo near-match DMA formatting issues detected.")

    # Cross-stream presence matrix
    print("\nDMA cross-stream presence matrix:")
    all_streams = sorted(dma_by_stream.keys())
    print(f"  {'DMA':<40} " + " ".join(f"{s:<15}" for s in all_streams))
    for dma in sorted(all_dma_values):
        flags = ["YES" if dma in dma_by_stream[s] else "---" for s in all_streams]
        print(f"  {dma:<40} " + " ".join(f"{f:<15}" for f in flags))


def analyze_state_standardization():
    """Section 2: State standardization across streams."""
    print("\n" + "=" * 80)
    print("SECTION 2: STATE STANDARDIZATION ANALYSIS")
    print("=" * 80)

    state_by_file = {}
    all_state_values = set()

    for f in PAID_SOCIAL_FILES + WEB_FILES + TXN_FILES:
        rows = read_csv(f)
        vals = {r.get("state", "") for r in rows if r.get("state")}
        state_by_file[f] = vals
        all_state_values.update(vals)

    state_by_stream = {}
    for stream, files in STREAM_GROUPS.items():
        combined = set()
        for f in files:
            combined.update(state_by_file[f])
        state_by_stream[stream] = combined

    print(f"\nTotal unique state values: {len(all_state_values)}")
    for stream, vals in state_by_stream.items():
        print(f"  {stream}: {len(vals)} unique states")

    print("\nAll unique state values (sorted):")
    for v in sorted(all_state_values):
        sources = []
        for stream, files in STREAM_GROUPS.items():
            for f in files:
                if v in state_by_file[f]:
                    sources.append(stream)
                    break
        print(f"  '{v}' -> {', '.join(sorted(set(sources)))}")

    abbrevs = [v for v in all_state_values if len(v) == 2 and v.isupper()]
    full_names = [v for v in all_state_values if len(v) > 2]
    print(f"\nFormat check:")
    print(f"  2-letter uppercase: {len(abbrevs)} -> {sorted(abbrevs)}")
    print(f"  Full names (>2 chars): {len(full_names)} -> {sorted(full_names)}")


def analyze_airport_mapping():
    """Section 3: Airport-to-geography mapping."""
    print("\n" + "=" * 80)
    print("SECTION 3: AIRPORT-TO-GEOGRAPHY MAPPING")
    print("=" * 80)

    ooh_rows = read_csv(OOH_FILE)
    ooh_headers = list(ooh_rows[0].keys()) if ooh_rows else []
    print(f"\nOOH file columns: {ooh_headers}")

    airport_map = {}
    for r in ooh_rows:
        code = r.get("airport_code", "")
        name = r.get("airport_name", "")
        if code:
            airport_map[code] = name

    print(f"\nUnique airports: {len(airport_map)}")
    for code in sorted(airport_map.keys()):
        print(f"  {code} -> {airport_map[code]}")

    geo_fields = [
        h for h in ooh_headers
        if any(g in h.lower() for g in
               ["state", "dma", "city", "region", "geo", "zip", "location"])
    ]
    print(f"\nGeographic fields in OOH data: {geo_fields if geo_fields else 'NONE'}")
    print("  -> External lookup needed to map airport_code to state/DMA")


def analyze_campaign_linkage():
    """Section 4: Campaign linkage across paid social and web analytics."""
    print("\n" + "=" * 80)
    print("SECTION 4: CAMPAIGN LINKAGE INVESTIGATION")
    print("=" * 80)

    ps_campaign_names = set()
    ps_campaign_ids = set()
    id_to_name = {}

    for f in PAID_SOCIAL_FILES:
        rows = read_csv(f)
        for r in rows:
            cn = r.get("campaign_name", "")
            ci = r.get("campaign_id", "")
            if cn:
                ps_campaign_names.add(cn)
            if ci:
                ps_campaign_ids.add(ci)
            if ci and cn:
                id_to_name[ci] = cn

    print(f"\nPaid Social - unique campaign_name values: {len(ps_campaign_names)}")
    for v in sorted(ps_campaign_names):
        print(f"  '{v}'")

    print(f"\nPaid Social - unique campaign_id values: {len(ps_campaign_ids)}")
    for v in sorted(ps_campaign_ids):
        print(f"  '{v}' -> {id_to_name.get(v, '?')}")

    # Web analytics
    web_campaigns = set()
    web_source_medium = set()
    web_campaign_source_medium = defaultdict(lambda: defaultdict(int))

    for f in WEB_FILES:
        rows = read_csv(f)
        for r in rows:
            c = r.get("campaign", "")
            src = r.get("traffic_source", "")
            med = r.get("traffic_medium", "")
            if c:
                web_campaigns.add(c)
            if src or med:
                web_source_medium.add((src, med))
            if c:
                web_campaign_source_medium[c][(src, med)] += 1

    print(f"\nWeb Analytics - unique campaign values: {len(web_campaigns)}")
    for v in sorted(web_campaigns):
        print(f"  '{v}'")

    print(f"\nWeb Analytics - source/medium combos: {len(web_source_medium)}")
    for src, med in sorted(web_source_medium):
        print(f"  source='{src}' / medium='{med}'")

    # Cross-reference
    exact_matches = ps_campaign_names & web_campaigns
    print(f"\n*** EXACT MATCHES: {len(exact_matches)} ***")
    for v in sorted(exact_matches):
        print(f"  '{v}'")

    print(f"\n*** PARTIAL/FUZZY MATCHES ***")
    for wc in sorted(web_campaigns):
        for pc in sorted(ps_campaign_names):
            if wc.lower() == pc.lower():
                continue
            if wc.lower() in pc.lower() or pc.lower() in wc.lower():
                print(f"  web '{wc}' <-> paid '{pc}' (substring match)")

    # Campaign theme extraction
    themes = set()
    for name in id_to_name.values():
        parts = name.split(" ", 1)
        if len(parts) == 2:
            themes.add(parts[1])
    print(f"\nPaid social campaign themes: {sorted(themes)}")

    # Cross-tab
    print(f"\nWeb campaign -> source/medium breakdown (row counts):")
    for c in sorted(web_campaign_source_medium.keys()):
        print(f"  campaign='{c}':")
        for (src, med), cnt in sorted(web_campaign_source_medium[c].items()):
            print(f"    source='{src}', medium='{med}' -> {cnt} rows")


def analyze_podcast_geography():
    """Section 5: Podcast geography signals."""
    print("\n" + "=" * 80)
    print("SECTION 5: PODCAST GEOGRAPHY SIGNALS")
    print("=" * 80)

    podcast_names = set()
    podcast_founder_mentions = defaultdict(set)

    for f in PODCAST_FILES:
        rows = read_csv(f)
        for r in rows:
            pn = r.get("podcast_name", "")
            if pn:
                podcast_names.add(pn)
                if r.get("mentions_founder", "0") == "1":
                    podcast_founder_mentions[pn].add(r.get("episode_title", ""))

    print(f"\nUnique podcast names: {len(podcast_names)}")

    geo_podcasts = {}
    non_geo_podcasts = []

    for pn in sorted(podcast_names):
        found_geo = []
        pn_lower = pn.lower()
        for s in US_STATES:
            if s.lower() in pn_lower:
                found_geo.append(f"state:{s}")
        for c in CITIES:
            if len(c) <= 3:
                if re.search(r"\b" + re.escape(c) + r"\b", pn):
                    found_geo.append(f"city:{c}")
            else:
                if c.lower() in pn_lower:
                    found_geo.append(f"city:{c}")
        for rt in REGIONAL:
            if rt.lower() in pn_lower:
                found_geo.append(f"regional:{rt}")
        for sa in STATE_ABBREVS:
            if re.search(r"\b" + re.escape(sa) + r"\b", pn):
                found_geo.append(f"abbrev:{sa}")

        if found_geo:
            geo_podcasts[pn] = found_geo
        else:
            non_geo_podcasts.append(pn)

    print("\nPodcasts WITH geographic references:")
    for pn, refs in sorted(geo_podcasts.items()):
        has_founder = "YES" if pn in podcast_founder_mentions else "NO"
        print(f"  '{pn}' -> {refs} | founder: {has_founder}")

    print(f"\nPodcasts WITHOUT geographic references:")
    for pn in sorted(non_geo_podcasts):
        has_founder = "YES" if pn in podcast_founder_mentions else "NO"
        n_eps = len(podcast_founder_mentions.get(pn, set()))
        print(f"  '{pn}' | founder: {has_founder} ({n_eps} episodes)")

    non_geo_with = [pn for pn in non_geo_podcasts if pn in podcast_founder_mentions]
    non_geo_without = [pn for pn in non_geo_podcasts if pn not in podcast_founder_mentions]
    print(f"\nNon-geo with founder mentions: {len(non_geo_with)}")
    print(f"Non-geo without founder mentions: {len(non_geo_without)}")


def main():
    analyze_dma_standardization()
    analyze_state_standardization()
    analyze_airport_mapping()
    analyze_campaign_linkage()
    analyze_podcast_geography()


if __name__ == "__main__":
    main()
