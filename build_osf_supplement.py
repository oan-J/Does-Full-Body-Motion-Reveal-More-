"""
Build OSF supplementary materials.
Reads from analysis_outputs_ISMAR/ and raw demographics tables.
Writes all outputs to osf_supplement/.
No participant-level data or IDs are written to any output file.
"""
import csv
import json
import math
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, "..")
OUT = BASE  # osf_supplement/
SCORED = os.path.join(ROOT, "analysis_outputs_ISMAR/data/scored_dataset.csv")
UB_DEMO = os.path.join(ROOT, "mocapcomparison_table_upperBodyDemographics.csv")
FB_DEMO = os.path.join(ROOT, "mocapcomparison_table_fullBodyDemographics.csv")


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────
# 1. Aggregate demographics
# ─────────────────────────────────────────────
def build_demographics():
    rows_ub = read_csv(UB_DEMO)
    rows_fb = read_csv(FB_DEMO)

    def tabulate(rows, condition):
        cols = ["age", "gender", "ethnicity", "mocap_experience"]
        out = []
        for col in cols:
            counts = defaultdict(int)
            for r in rows:
                cat = r[col]
                # merge multi-select ethnicity responses into one category
                if col == "ethnicity" and ";" in cat:
                    cat = "multiracial"
                counts[cat] += 1
            n_total = len(rows)
            for cat, n in sorted(counts.items()):
                pct = round(100.0 * n / n_total, 1)
                out.append({
                    "condition": condition,
                    "attribute": col,
                    "category": cat,
                    "n": n,
                    "percent": pct,
                    "total_n": n_total,
                })
        return out

    rows_out = tabulate(rows_ub, "upper_body") + tabulate(rows_fb, "full_body")

    path = os.path.join(OUT, "demographics_aggregate.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["condition", "attribute", "category", "n", "percent", "total_n"])
        w.writeheader()
        w.writerows(rows_out)
    print(f"Wrote {path}  ({len(rows_out)} rows)")


# ─────────────────────────────────────────────
# 2. Ratings per clip (aggregated, no PII)
# ─────────────────────────────────────────────
ATTRS = ["gender", "age", "height", "weight", "ethnicity"]

RESPONSE_COLS = {
    "gender":    ("user_gender",    "user_gender_confidence",    "gender_correct",    "correct_gender"),
    "age":       ("user_age",       "user_age_confidence",       "age_correct",       "correct_age_group"),
    "height":    ("user_height",    "user_height_confidence",    "height_correct",    "correct_height_cm"),
    "weight":    ("user_weight",    "user_weight_confidence",    "weight_correct",    "correct_weight_kg"),
    "ethnicity": ("user_ethnicity", "user_ethnicity_confidence", "ethnicity_correct", "correct_ethnicity"),
}


def build_ratings_per_clip():
    rows = read_csv(SCORED)
    # group by (video_file, condition, attribute)
    # structure: {(video, cond, attr): {"responses": [...], "confs": [...], "correct": int, "gt": str}}
    data = defaultdict(lambda: {"responses": [], "confs": [], "correct": 0, "gt": None})

    for row in rows:
        vf = row["video_file"]
        cond = row["condition"]
        for attr, (resp_col, conf_col, corr_col, gt_col) in RESPONSE_COLS.items():
            key = (vf, cond, attr)
            data[key]["responses"].append(row[resp_col])
            try:
                data[key]["confs"].append(float(row[conf_col]))
            except (ValueError, KeyError):
                pass
            data[key]["correct"] += int(row[corr_col]) if row[corr_col] in ("1", "True", "true") else 0
            if data[key]["gt"] is None:
                data[key]["gt"] = row[gt_col]

    out_rows = []
    for (vf, cond, attr), d in sorted(data.keys().__iter__() and iter(sorted(data.items()))):
        n = len(d["responses"])
        # response distribution
        dist = defaultdict(int)
        for r in d["responses"]:
            dist[r] += 1
        dist_json = json.dumps(dict(sorted(dist.items())), ensure_ascii=False)
        dist_pct = {k: round(100.0 * v / n, 1) for k, v in dist.items()}
        dist_pct_json = json.dumps(dict(sorted(dist_pct.items())), ensure_ascii=False)
        # confidence
        confs = d["confs"]
        mean_conf = round(sum(confs) / len(confs), 3) if confs else ""
        # std dev
        if len(confs) > 1:
            var = sum((c - mean_conf) ** 2 for c in confs) / (len(confs) - 1)
            sd_conf = round(math.sqrt(var), 3)
        else:
            sd_conf = ""
        accuracy = round(d["correct"] / n, 4) if n > 0 else ""

        # parse nymeria_id and timestamps from video filename
        fname = vf.replace(".mp4", "")
        parts = fname.rsplit("_", 2)
        if len(parts) == 3:
            nymeria_id, start_s, end_s = parts
        else:
            nymeria_id, start_s, end_s = fname, "", ""

        out_rows.append({
            "clip_id": vf,
            "nymeria_sequence_id": nymeria_id,
            "condition": cond,
            "attribute": attr,
            "ground_truth": d["gt"],
            "n_responses": n,
            "accuracy": accuracy,
            "response_counts": dist_json,
            "response_pct": dist_pct_json,
            "mean_confidence": mean_conf,
            "sd_confidence": sd_conf,
        })

    path = os.path.join(OUT, "ratings_per_clip.csv")
    fieldnames = ["clip_id", "nymeria_sequence_id", "condition", "attribute",
                  "ground_truth", "n_responses", "accuracy",
                  "response_counts", "response_pct", "mean_confidence", "sd_confidence"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {path}  ({len(out_rows)} rows)")
    return out_rows


# ─────────────────────────────────────────────
# 3. Stimuli manifest
# ─────────────────────────────────────────────
def build_stimuli_manifest():
    rows = read_csv(SCORED)
    seen = {}
    for row in rows:
        vf = row["video_file"]
        if vf in seen:
            continue
        fname = vf.replace(".mp4", "")
        parts = fname.rsplit("_", 2)
        if len(parts) == 3:
            nymeria_id, start_s, end_s = parts
        else:
            nymeria_id, start_s, end_s = fname, "", ""
        seen[vf] = {
            "clip_id": vf,
            "nymeria_sequence_id": nymeria_id,
            "start_sec": start_s,
            "end_sec": end_s,
            "duration_sec": int(end_s) - int(start_s) if start_s and end_s else "",
            "conditions": "upper_body,full_body",
            "ground_truth_gender": row["correct_gender"],
            "ground_truth_age_group": row["correct_age_group"],
            "ground_truth_height_cm": row["correct_height_cm"],
            "ground_truth_weight_kg": row["correct_weight_kg"],
            "ground_truth_ethnicity": row["correct_ethnicity"],
            "height_normalization": "uniform_scale_max_dim_1.8",
        }

    path = os.path.join(OUT, "stimuli_manifest.csv")
    fieldnames = [
        "clip_id", "nymeria_sequence_id", "start_sec", "end_sec", "duration_sec",
        "conditions",
        "ground_truth_gender", "ground_truth_age_group",
        "ground_truth_height_cm", "ground_truth_weight_kg", "ground_truth_ethnicity",
        "height_normalization",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(sorted(seen.values(), key=lambda r: r["clip_id"]))
    print(f"Wrote {path}  ({len(seen)} rows)")


# ─────────────────────────────────────────────
# 4. Gender–height correlation (clip level)
# ─────────────────────────────────────────────
def build_gender_height_correlation():
    """
    Clip-level: for each clip×condition, compute
    - prop_guessed_male (gender response = Male)
    - mean_height_response_midpoint  (midpoint of the chosen height bin)
    then correlate across clips (Pearson r).
    """
    HEIGHT_BIN_MID = {
        "130-140": 135, "140-150": 145, "150-160": 155, "160-170": 165,
        "170-180": 175, "180-190": 185, "190-200": 195, "200+": 205,
        # handle variants
        "<130": 125, "under 130": 125,
    }

    # Build clip-level aggregates from raw scored data (still no participant IDs exported)
    rows = read_csv(SCORED)

    # clip×condition → {n, n_male_gender, height_mids}
    clip_data = defaultdict(lambda: {"n": 0, "n_male_gender": 0, "height_mids": []})
    for row in rows:
        key = (row["video_file"], row["condition"])
        clip_data[key]["n"] += 1
        if row["user_gender"] == "Male":
            clip_data[key]["n_male_gender"] += 1
        mid = HEIGHT_BIN_MID.get(row["user_height"])
        if mid is not None:
            clip_data[key]["height_mids"].append(mid)

    # Compute clip-level stats
    clip_stats = []
    for (vf, cond), d in sorted(clip_data.items()):
        n = d["n"]
        if n == 0:
            continue
        prop_male = d["n_male_gender"] / n
        hm = d["height_mids"]
        mean_height = sum(hm) / len(hm) if hm else None

        fname = vf.replace(".mp4", "")
        parts = fname.rsplit("_", 2)
        nymeria_id = parts[0] if len(parts) == 3 else fname

        clip_stats.append({
            "clip_id": vf,
            "nymeria_sequence_id": nymeria_id,
            "condition": cond,
            "n": n,
            "prop_guessed_male": round(prop_male, 4),
            "mean_height_response_midpoint_cm": round(mean_height, 2) if mean_height is not None else "",
        })

    # Pearson r at clip level (per condition)
    def pearson(xs, ys):
        n = len(xs)
        if n < 3:
            return None, None
        mx, my = sum(xs) / n, sum(ys) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        if dx == 0 or dy == 0:
            return None, None
        r = num / (dx * dy)
        # t statistic for H0: r = 0, df = n - 2
        if abs(r) >= 1.0:
            return r, float("inf")
        t = r * math.sqrt(n - 2) / math.sqrt(1 - r ** 2)
        return r, t

    for cond in ["upper_body", "full_body"]:
        subset = [s for s in clip_stats if s["condition"] == cond
                  and s["mean_height_response_midpoint_cm"] != ""]
        xs = [s["prop_guessed_male"] for s in subset]
        ys = [float(s["mean_height_response_midpoint_cm"]) for s in subset]
        r, t = pearson(xs, ys)
        if r is not None:
            n = len(subset)
            print(f"  Clip-level Pearson r ({cond}): r={r:.3f}, t({n-2})={t:.3f}, n={n} clips")

    # Save clip-level CSV
    path_clips = os.path.join(OUT, "analysis", "gender_height_clip_level.csv")
    with open(path_clips, "w", newline="") as f:
        fieldnames = ["clip_id", "nymeria_sequence_id", "condition", "n",
                      "prop_guessed_male", "mean_height_response_midpoint_cm"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(clip_stats)
    print(f"  Wrote {path_clips}  ({len(clip_stats)} rows)")

    # Save summary results
    results = []
    for cond in ["upper_body", "full_body"]:
        subset = [s for s in clip_stats if s["condition"] == cond
                  and s["mean_height_response_midpoint_cm"] != ""]
        xs = [s["prop_guessed_male"] for s in subset]
        ys = [float(s["mean_height_response_midpoint_cm"]) for s in subset]
        r, t = pearson(xs, ys)
        n = len(subset)
        results.append({
            "level": "clip",
            "condition": cond,
            "n_units": n,
            "statistic": "Pearson_r",
            "r": round(r, 4) if r is not None else "",
            "t_statistic": round(t, 3) if t is not None else "",
            "df": n - 2,
            "note": "prop_guessed_male vs mean_height_response_midpoint",
        })
    path_results = os.path.join(OUT, "analysis", "gender_height_correlation_results.csv")
    with open(path_results, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["level", "condition", "n_units", "statistic", "r",
                                          "t_statistic", "df", "note"])
        w.writeheader()
        w.writerows(results)
    print(f"  Wrote {path_results}")


# ─────────────────────────────────────────────
# Privacy scan
# ─────────────────────────────────────────────
def privacy_scan():
    """Check that no participant_id, worker ID or timestamps appear in output CSVs."""
    rows_raw = read_csv(SCORED)
    participant_ids = set(r["participant_id"] for r in rows_raw)

    issues = []
    for fname in os.listdir(OUT):
        if not fname.endswith(".csv"):
            continue
        fpath = os.path.join(OUT, fname)
        with open(fpath) as f:
            content = f.read()
        for pid in participant_ids:
            if pid in content:
                issues.append(f"  {fname}: contains participant_id {pid}")
        for col in ["participant_id", "worker_id", "prolific_id"]:
            if col in content.lower():
                issues.append(f"  {fname}: column name '{col}' found")

    # also check analysis subdir
    for fname in os.listdir(os.path.join(OUT, "analysis")):
        if not fname.endswith(".csv"):
            continue
        with open(os.path.join(OUT, "analysis", fname)) as f:
            content = f.read()
        for pid in participant_ids:
            if pid in content:
                issues.append(f"  analysis/{fname}: contains participant_id {pid}")

    if issues:
        print("PRIVACY ISSUES FOUND:")
        for i in issues:
            print(i)
    else:
        print("Privacy scan: PASSED — no participant IDs found in any output CSV.")
    return len(issues) == 0


if __name__ == "__main__":
    print("=== Demographics ===")
    build_demographics()

    print("\n=== Ratings per clip ===")
    build_ratings_per_clip()

    print("\n=== Stimuli manifest ===")
    build_stimuli_manifest()

    print("\n=== Gender–height correlation ===")
    build_gender_height_correlation()

    print("\n=== Privacy scan ===")
    privacy_scan()

    print("\nDone.")
