"""
Grain Analysis & Metric Feasibility — Pre-schema design investigation.

Determines natural grain (unique key) for each data stream, verifies metric
formulas, checks date spine coverage, and flags data quality issues.

Outputs: docs/grain_analysis.md
Run:     python -m src.exploration.grain_analysis
"""

import csv
import os
import random
import statistics
from collections import defaultdict, Counter
from datetime import date, timedelta

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

ORGANIC_FILES = [
    "sBelles_tiktok_owned_2023.csv",
    "sBelles_tiktok_owned_2024.csv",
]

PODCAST_FILES = [
    "sBelles_podcast_mentions_2023_2024_part1.csv",
    "sBelles_podcast_mentions_2023_2024_part2.csv",
]

OOH_FILE = "sBelles_ooh_airport_weekly.csv"


def read_csv(filename):
    path = os.path.join(DATA, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_key_uniqueness(rows, key_cols):
    """Test if a combination of columns forms a unique key. Returns dupe count."""
    if any(c not in rows[0] for c in key_cols):
        return None  # column missing
    seen = set()
    dupes = 0
    for r in rows:
        key = tuple(r.get(c, "") for c in key_cols)
        if key in seen:
            dupes += 1
        else:
            seen.add(key)
    return dupes


# =========================================================================
# SECTION 1: FACT TABLE GRAIN ANALYSIS
# =========================================================================

def analyze_paid_social_grain():
    """1a. Paid social grain analysis."""
    print("=" * 80)
    print("1a. PAID SOCIAL GRAIN ANALYSIS")
    print("=" * 80)

    candidate_keys = [
        ("date", "channel", "campaign_id", "dma_name"),
        ("date", "channel", "campaign_id", "dma_name", "optimization_goal"),
        ("date", "channel", "campaign_id", "dma_name", "age_target"),
        ("date", "channel", "campaign_id", "dma_name", "audience_segment"),
        ("date", "channel", "campaign_id", "dma_name", "age_target",
         "audience_segment"),
        ("date", "channel", "campaign_id", "dma_name", "optimization_goal",
         "age_target", "audience_segment"),
    ]

    for f in PAID_SOCIAL_FILES:
        rows = read_csv(f)
        print(f"\n{f} ({len(rows)} rows)")
        for ck in candidate_keys:
            dupes = test_key_uniqueness(rows, ck)
            if dupes is None:
                print(f"  Key {ck}: SKIPPED (missing column)")
            else:
                status = "UNIQUE" if dupes == 0 else f"{dupes} duplicates"
                print(f"  Key {ck}: {status}")

    # Sample rows
    print("\nSample 5 rows (paid_instagram_part1):")
    sample_rows = read_csv(PAID_SOCIAL_FILES[0])
    random.seed(42)
    for r in random.sample(sample_rows, 5):
        print(
            f"  date={r['date']} channel={r['channel']} "
            f"campaign={r['campaign_name']} dma={r['dma_name']} "
            f"age={r.get('age_target', '')} "
            f"audience={r.get('audience_segment', '')} "
            f"opt={r.get('optimization_goal', '')}"
        )


def analyze_web_grain():
    """1b. Web analytics grain analysis."""
    print("\n" + "=" * 80)
    print("1b. WEB ANALYTICS GRAIN ANALYSIS")
    print("=" * 80)

    all_rows = []
    for f in WEB_FILES:
        all_rows.extend(read_csv(f))

    print(f"\nTotal web rows: {len(all_rows)}")

    # Unique dimension values
    sources = sorted(set(r["traffic_source"] for r in all_rows))
    mediums = sorted(set(r["traffic_medium"] for r in all_rows))
    devices = sorted(set(r["device_category"] for r in all_rows))
    print(f"Unique traffic_source: {sources}")
    print(f"Unique traffic_medium: {mediums}")
    print(f"Unique device_category: {devices}")

    # Key uniqueness
    key_cols = ("event_datetime", "user_id", "session_id", "page_url")
    dupes = test_key_uniqueness(all_rows, key_cols)
    print(f"\nKey {key_cols}: "
          f"{'UNIQUE' if dupes == 0 else f'{dupes} duplicates'}")

    # Cross-file overlap
    keys_by_file = {}
    for f in WEB_FILES:
        rows = read_csv(f)
        keys = set()
        for r in rows:
            keys.add((r["event_datetime"], r["user_id"],
                       r["session_id"], r["page_url"]))
        keys_by_file[f] = keys

    print("\nCross-file overlap check:")
    for i, f1 in enumerate(WEB_FILES):
        for f2 in WEB_FILES[i + 1:]:
            overlap = keys_by_file[f1] & keys_by_file[f2]
            print(f"  {f1} & {f2}: {len(overlap)} overlapping keys")

    # Overlap date range detail
    web_q3q4 = read_csv(WEB_FILES[1])
    web_q1_24 = read_csv(WEB_FILES[2])
    dates_q3q4 = sorted(set(r["event_datetime"][:10] for r in web_q3q4))
    dates_q1_24 = sorted(set(r["event_datetime"][:10] for r in web_q1_24))
    overlap_dates = sorted(set(dates_q3q4) & set(dates_q1_24))
    if overlap_dates:
        print(f"\n  Q3Q4 2023: {dates_q3q4[0]} to {dates_q3q4[-1]}")
        print(f"  Q1 2024:   {dates_q1_24[0]} to {dates_q1_24[-1]}")
        print(f"  Overlap:   {overlap_dates[0]} to {overlap_dates[-1]} "
              f"({len(overlap_dates)} days)")
        overlap_set = set(overlap_dates)
        q3q4_overlap = [r for r in web_q3q4
                        if r["event_datetime"][:10] in overlap_set]
        q1_overlap = [r for r in web_q1_24
                      if r["event_datetime"][:10] in overlap_set]
        print(f"  Rows in Q3Q4 for overlap dates: {len(q3q4_overlap)}")
        print(f"  Rows in Q1 2024 for overlap dates: {len(q1_overlap)}")
        identical = (set(tuple(r.values()) for r in q3q4_overlap)
                     & set(tuple(r.values()) for r in q1_overlap))
        print(f"  Byte-identical rows: {len(identical)}")

    # Sessions/users per day (sample)
    daily_sessions = defaultdict(set)
    daily_users = defaultdict(set)
    for r in all_rows:
        day = r["event_datetime"][:10]
        daily_sessions[day].add(r["session_id"])
        daily_users[day].add(r["user_id"])

    sample_days = (sorted(daily_sessions.keys())[:3]
                   + sorted(daily_sessions.keys())[-3:])
    print(f"\nSessions/users per day (sample):")
    for d in sample_days:
        print(f"  {d}: {len(daily_sessions[d])} sessions, "
              f"{len(daily_users[d])} users")


def analyze_ecommerce_grain():
    """1c. Ecommerce grain analysis."""
    print("\n" + "=" * 80)
    print("1c. ECOMMERCE GRAIN ANALYSIS")
    print("=" * 80)

    all_txn = []
    for f in TXN_FILES:
        all_txn.extend(read_csv(f))

    print(f"\nTotal transaction rows: {len(all_txn)}")

    order_counts = Counter(r["order_id"] for r in all_txn)
    multi_line = {oid: cnt for oid, cnt in order_counts.items() if cnt > 1}
    single_line = {oid: cnt for oid, cnt in order_counts.items() if cnt == 1}
    print(f"Unique order_ids: {len(order_counts)}")
    print(f"Orders with 1 line item: {len(single_line)}")
    print(f"Orders with >1 line items: {len(multi_line)}")

    line_item_dist = Counter(order_counts.values())
    print(f"Line items per order distribution:")
    for n, cnt in sorted(line_item_dist.items()):
        print(f"  {n} line items: {cnt} orders")
    avg_lines = sum(order_counts.values()) / len(order_counts)
    print(f"Average line items per order: {avg_lines:.2f}")

    # Unique dimension values
    categories = sorted(set(r["product_category"] for r in all_txn))
    sizes = sorted(set(r["size"] for r in all_txn))
    promos = sorted(set(r["promo_flag"] for r in all_txn))
    print(f"\nUnique product_category: {categories}")
    print(f"Unique size: {sizes}")
    print(f"Unique promo_flag: {promos}")

    # Order value stats
    order_revenue = defaultdict(float)
    for r in all_txn:
        order_revenue[r["order_id"]] += float(r["line_revenue"])
    avg_ov = sum(order_revenue.values()) / len(order_revenue)
    print(f"\nAverage order value: ${avg_ov:.2f}")
    print(f"Min order value: ${min(order_revenue.values()):.2f}")
    print(f"Max order value: ${max(order_revenue.values()):.2f}")


def analyze_organic_social_grain():
    """1d. Organic social grain analysis."""
    print("\n" + "=" * 80)
    print("1d. ORGANIC SOCIAL GRAIN ANALYSIS")
    print("=" * 80)

    all_organic = []
    for f in ORGANIC_FILES:
        all_organic.extend(read_csv(f))

    print(f"\nTotal organic social rows: {len(all_organic)}")

    date_counts = Counter(r["date"] for r in all_organic)
    multi_date = {d: c for d, c in date_counts.items() if c > 1}
    print(f"Unique dates: {len(date_counts)}")
    print(f"Dates with >1 row: {len(multi_date)}")
    if multi_date:
        print(f"  Sample: {list(multi_date.items())[:5]}")

    post_id_counts = Counter(r["post_id"] for r in all_organic)
    dup_posts = {p: c for p, c in post_id_counts.items() if c > 1}
    print(f"Unique post_ids: {len(post_id_counts)}")
    print(f"Duplicate post_ids: {len(dup_posts)}")

    dp_dupes = test_key_uniqueness(all_organic, ("date", "post_id"))
    print(f"Key (date, post_id): "
          f"{'UNIQUE' if dp_dupes == 0 else f'{dp_dupes} duplicates'}")

    # Post ID recycling across files
    org1 = read_csv(ORGANIC_FILES[0])
    org2 = read_csv(ORGANIC_FILES[1])
    ids1 = set(r["post_id"] for r in org1)
    ids2 = set(r["post_id"] for r in org2)
    overlap = ids1 & ids2
    print(f"\nPost ID overlap between files:")
    print(f"  2023 file post_ids: {len(ids1)}")
    print(f"  2024 file post_ids: {len(ids2)}")
    print(f"  Overlapping: {len(overlap)} (post IDs are recycled across years)")

    if overlap:
        print("  Sample overlapping posts:")
        for pid in list(overlap)[:3]:
            r1 = next(r for r in org1 if r["post_id"] == pid)
            r2 = next(r for r in org2 if r["post_id"] == pid)
            print(f"    {pid}: 2023={r1['date']}/{r1['followers']}fol, "
                  f"2024={r2['date']}/{r2['followers']}fol")

    # Followers monotonicity
    all_organic.sort(key=lambda r: (r["date"], r["post_id"]))
    daily_followers = {}
    for r in all_organic:
        if r["date"] not in daily_followers:
            daily_followers[r["date"]] = int(r["followers"])

    dates_sorted = sorted(daily_followers.keys())
    print(f"\nFollowers: {dates_sorted[0]}={daily_followers[dates_sorted[0]]} "
          f"-> {dates_sorted[-1]}={daily_followers[dates_sorted[-1]]}")

    decreases = 0
    for i in range(1, len(dates_sorted)):
        if daily_followers[dates_sorted[i]] < daily_followers[dates_sorted[i - 1]]:
            decreases += 1
    print(f"Day-over-day decreases: {decreases}/{len(dates_sorted) - 1} "
          f"({100 * decreases / (len(dates_sorted) - 1):.1f}%)")

    # Inconsistent follower counts within same day
    daily_vals = defaultdict(set)
    for r in all_organic:
        daily_vals[r["date"]].add(int(r["followers"]))
    inconsistent = sum(1 for vals in daily_vals.values() if len(vals) > 1)
    print(f"Days with inconsistent follower counts across posts: {inconsistent}")


def analyze_podcast_grain():
    """1e. Podcast grain analysis."""
    print("\n" + "=" * 80)
    print("1e. PODCAST GRAIN ANALYSIS")
    print("=" * 80)

    all_podcast = []
    for f in PODCAST_FILES:
        all_podcast.extend(read_csv(f))

    print(f"\nTotal podcast rows: {len(all_podcast)}")

    pk_dupes = test_key_uniqueness(
        all_podcast, ("podcast_name", "episode_title", "mention_datetime"))
    print(f"Key (podcast_name, episode_title, mention_datetime): "
          f"{'UNIQUE' if pk_dupes == 0 else f'{pk_dupes} duplicates'}")

    # Release date vs mention date
    same = sum(1 for r in all_podcast
               if r["episode_release_date"] == r["mention_datetime"][:10])
    diff = len(all_podcast) - same
    print(f"\nRelease date == mention date: {same}")
    print(f"Release date != mention date: {diff}")

    # Unique values
    sentiments = Counter(r["sentiment"] for r in all_podcast)
    podcasts = sorted(set(r["podcast_name"] for r in all_podcast))
    print(f"\nSentiment: {dict(sentiments)}")
    print(f"Podcasts: {podcasts}")

    # Episodes per podcast
    eps = defaultdict(set)
    for r in all_podcast:
        eps[r["podcast_name"]].add(r["episode_title"])
    print("\nEpisodes per podcast:")
    for pn in sorted(eps):
        print(f"  {pn}: {len(eps[pn])}")

    # Multi-mention episodes
    ep_counts = Counter(
        (r["podcast_name"], r["episode_title"]) for r in all_podcast)
    multi = {k: v for k, v in ep_counts.items() if v > 1}
    print(f"\nEpisodes with >1 mention row: {len(multi)}")
    for (pn, ep), cnt in multi.items():
        print(f"  '{pn}' / '{ep}': {cnt} rows")


def analyze_ooh_grain():
    """1f. OOH grain analysis."""
    print("\n" + "=" * 80)
    print("1f. OOH GRAIN ANALYSIS")
    print("=" * 80)

    ooh = read_csv(OOH_FILE)
    print(f"\nTotal OOH rows: {len(ooh)}")

    ooh_keys = [
        ("week_start_date", "airport_code"),
        ("week_start_date", "airport_code", "format"),
        ("week_start_date", "airport_code", "audience_segment"),
        ("week_start_date", "airport_code", "format", "audience_segment"),
    ]
    for ck in ooh_keys:
        dupes = test_key_uniqueness(ooh, ck)
        print(f"Key {ck}: {'UNIQUE' if dupes == 0 else f'{dupes} duplicates'}")

    formats = sorted(set(r["format"] for r in ooh))
    segments = sorted(set(r["audience_segment"] for r in ooh))
    print(f"\nUnique format: {formats}")
    print(f"Unique audience_segment: {segments}")


# =========================================================================
# SECTION 2: METRIC FEASIBILITY
# =========================================================================

def verify_ecommerce_metrics():
    """2a. Ecommerce revenue formula and discount analysis."""
    print("\n" + "=" * 80)
    print("2a. ECOMMERCE REVENUE FORMULA VERIFICATION")
    print("=" * 80)

    all_txn = []
    for f in TXN_FILES:
        all_txn.extend(read_csv(f))

    # Verify formula on 20 random rows
    random.seed(42)
    sample = random.sample(all_txn, 20)
    print("\nVerifying: line_revenue = quantity * unit_price "
          "- discount_per_unit * quantity")
    print(f"{'qty':>4} {'unit_price':>10} {'discount':>10} "
          f"{'expected':>10} {'actual':>10} {'match':>6}")

    for r in sample:
        qty = int(r["quantity"])
        up = float(r["unit_price"])
        disc = float(r["discount_per_unit"])
        expected = qty * up - disc * qty
        actual = float(r["line_revenue"])
        match = abs(expected - actual) < 0.01
        print(f"{qty:>4} {up:>10.2f} {disc:>10.2f} {expected:>10.2f} "
              f"{actual:>10.2f} {'YES' if match else '**NO**':>6}")

    # Full verification
    all_mismatches = sum(
        1 for r in all_txn
        if abs((int(r["quantity"]) * float(r["unit_price"])
                - float(r["discount_per_unit"]) * int(r["quantity"]))
               - float(r["line_revenue"])) >= 0.01
    )
    print(f"\nTotal mismatches across ALL {len(all_txn)} rows: {all_mismatches}")

    # Discount range
    discounts = [float(r["discount_per_unit"]) for r in all_txn]
    print(f"\nDiscount range: ${min(discounts):.2f} to ${max(discounts):.2f}")
    print(f"Mean discount: ${statistics.mean(discounts):.2f}")
    zero_disc = sum(1 for d in discounts if d == 0)
    print(f"Zero discount: {zero_disc} ({100 * zero_disc / len(discounts):.1f}%)")
    print(f"Non-zero discount: {len(discounts) - zero_disc} "
          f"({100 * (len(discounts) - zero_disc) / len(discounts):.1f}%)")

    # Promo flag
    promo_counts = Counter(r["promo_flag"] for r in all_txn)
    print(f"\nPromo flag distribution:")
    for k, v in sorted(promo_counts.items()):
        print(f"  promo_flag={k}: {v} ({100 * v / len(all_txn):.1f}%)")

    # Cross-tab promo vs discount
    promo_disc = sum(1 for r in all_txn
                     if r["promo_flag"] == "1"
                     and float(r["discount_per_unit"]) > 0)
    promo_no_disc = sum(1 for r in all_txn
                        if r["promo_flag"] == "1"
                        and float(r["discount_per_unit"]) == 0)
    no_promo_disc = sum(1 for r in all_txn
                        if r["promo_flag"] == "0"
                        and float(r["discount_per_unit"]) > 0)
    no_promo_no_disc = sum(1 for r in all_txn
                           if r["promo_flag"] == "0"
                           and float(r["discount_per_unit"]) == 0)
    print(f"\nPromo vs discount cross-tab:")
    print(f"  promo=1 & discount>0: {promo_disc}")
    print(f"  promo=1 & discount=0: {promo_no_disc}")
    print(f"  promo=0 & discount>0: {no_promo_disc}")
    print(f"  promo=0 & discount=0: {no_promo_no_disc}")

    # Negative revenue
    neg_rev = [r for r in all_txn if float(r["line_revenue"]) < 0]
    print(f"\nNegative line_revenue rows: {len(neg_rev)}")
    for r in neg_rev[:5]:
        print(f"  order={r['order_id']} qty={r['quantity']} "
              f"up={r['unit_price']} disc={r['discount_per_unit']} "
              f"rev={r['line_revenue']} promo={r['promo_flag']}")


def verify_organic_followers():
    """2b. Organic social followers monotonicity check."""
    print("\n" + "=" * 80)
    print("2b. ORGANIC SOCIAL FOLLOWERS ANALYSIS")
    print("=" * 80)

    all_organic = []
    for f in ORGANIC_FILES:
        all_organic.extend(read_csv(f))

    all_organic.sort(key=lambda r: (r["date"], r["post_id"]))
    daily_followers = {}
    for r in all_organic:
        if r["date"] not in daily_followers:
            daily_followers[r["date"]] = int(r["followers"])

    dates_sorted = sorted(daily_followers.keys())
    print(f"\nFirst: {dates_sorted[0]} = {daily_followers[dates_sorted[0]]}")
    print(f"Last:  {dates_sorted[-1]} = {daily_followers[dates_sorted[-1]]}")

    decreases = []
    for i in range(1, len(dates_sorted)):
        prev_d = dates_sorted[i - 1]
        curr_d = dates_sorted[i]
        if daily_followers[curr_d] < daily_followers[prev_d]:
            decreases.append((prev_d, daily_followers[prev_d],
                              curr_d, daily_followers[curr_d]))

    print(f"\nDecreases: {len(decreases)}/{len(dates_sorted) - 1} transitions")
    if decreases:
        print("First 10:")
        for pd, pv, cd, cv in decreases[:10]:
            print(f"  {pd} ({pv}) -> {cd} ({cv}): delta={cv - pv}")

    # Same-day inconsistency
    daily_vals = defaultdict(set)
    for r in all_organic:
        daily_vals[r["date"]].add(int(r["followers"]))
    inconsistent = {d: vals for d, vals in daily_vals.items() if len(vals) > 1}
    print(f"\nDays with inconsistent follower counts: {len(inconsistent)}")
    for d, vals in list(inconsistent.items())[:3]:
        print(f"  {d}: {sorted(vals)}")


def verify_podcast_metrics():
    """2c. Podcast impression and sentiment distributions."""
    print("\n" + "=" * 80)
    print("2c. PODCAST METRICS")
    print("=" * 80)

    all_podcast = []
    for f in PODCAST_FILES:
        all_podcast.extend(read_csv(f))

    impressions = [float(r["estimated_impressions"]) for r in all_podcast]
    print(f"\nEstimated impressions:")
    print(f"  Min: {min(impressions):,.0f}")
    print(f"  Max: {max(impressions):,.0f}")
    print(f"  Mean: {statistics.mean(impressions):,.0f}")
    print(f"  Median: {statistics.median(impressions):,.0f}")
    print(f"  Stdev: {statistics.stdev(impressions):,.0f}")

    sentiments = Counter(r["sentiment"] for r in all_podcast)
    print(f"\nSentiment distribution:")
    for k, v in sorted(sentiments.items()):
        print(f"  {k}: {v} ({100 * v / len(all_podcast):.1f}%)")

    ratings = [float(r["episode_rating"]) for r in all_podcast]
    print(f"\nEpisode rating: {min(ratings):.1f} – {max(ratings):.1f}, "
          f"mean={statistics.mean(ratings):.1f}, "
          f"median={statistics.median(ratings):.1f}")


# =========================================================================
# SECTION 3: DATE SPINE CHECK
# =========================================================================

def check_date_spine():
    """Check date coverage across all streams."""
    print("\n" + "=" * 80)
    print("SECTION 3: DATE SPINE CHECK")
    print("=" * 80)

    stream_dates = {
        "paid_social": set(),
        "web_analytics": set(),
        "ecommerce": set(),
        "organic_social": set(),
        "podcast": set(),
        "ooh": set(),
    }

    for f in PAID_SOCIAL_FILES:
        for r in read_csv(f):
            stream_dates["paid_social"].add(r["date"][:10])
    for f in WEB_FILES:
        for r in read_csv(f):
            stream_dates["web_analytics"].add(r["event_datetime"][:10])
    for f in TXN_FILES:
        for r in read_csv(f):
            stream_dates["ecommerce"].add(r["order_datetime"][:10])
    for f in ORGANIC_FILES:
        for r in read_csv(f):
            stream_dates["organic_social"].add(r["date"][:10])
    for f in PODCAST_FILES:
        for r in read_csv(f):
            stream_dates["podcast"].add(r["episode_release_date"][:10])
    for r in read_csv(OOH_FILE):
        stream_dates["ooh"].add(r["week_start_date"][:10])

    all_dates = set()
    for dates in stream_dates.values():
        all_dates.update(dates)

    min_date = min(all_dates)
    max_date = max(all_dates)
    print(f"\nEarliest date: {min_date}")
    print(f"Latest date: {max_date}")

    start = date.fromisoformat(min_date)
    end = date.fromisoformat(max_date)
    full_spine = set()
    d = start
    while d <= end:
        full_spine.add(d.isoformat())
        d += timedelta(days=1)

    missing = sorted(full_spine - all_dates)
    print(f"\nTotal days in range: {len(full_spine)}")
    print(f"Days with data: {len(all_dates & full_spine)}")
    print(f"Days with NO data: {len(missing)}")
    if missing:
        print(f"Missing: {missing[:20]}{'...' if len(missing) > 20 else ''}")

    print("\nPer-stream coverage:")
    for stream, dates in sorted(stream_dates.items()):
        print(f"  {stream}: {min(dates)} to {max(dates)} ({len(dates)} days)")


def main():
    # Section 1: Grain
    analyze_paid_social_grain()
    analyze_web_grain()
    analyze_ecommerce_grain()
    analyze_organic_social_grain()
    analyze_podcast_grain()
    analyze_ooh_grain()

    # Section 2: Metric feasibility
    verify_ecommerce_metrics()
    verify_organic_followers()
    verify_podcast_metrics()

    # Section 3: Date spine
    check_date_spine()


if __name__ == "__main__":
    main()
