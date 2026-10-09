# Does Full-Body Motion Reveal More? Comparing Human Inference of Personal Attributes from Upper-Body and Full-Body Motion

**Jiayi Liu**<sup>1</sup>, **Arran Zeyu Wang**<sup>1</sup>, **Mark Roman Miller**<sup>2</sup>, **Danielle Szafir**<sup>1</sup>, **William Payne**<sup>1</sup>

<sup>1</sup>University of North Carolina at Chapel Hill &nbsp;&nbsp; <sup>2</sup>Illinois Institute of Technology

*IEEE ISMAR 2026 (Poster)*

[**Paper & supplementary materials (OSF)**](https://osf.io/3enug/overview?view_only=25fe8c7e3d064e2ba722912ceccdfd39)

---

## Summary

This repository shares aggregate data from our between-subjects online study
(N = 120 Prolific participants; 60 upper-body, 60 full-body). Participants
watched 15-second skeletal walking clips of 18 subjects from the Nymeria
dataset and inferred each subject's gender, age, height, weight, and
ethnicity, rating their confidence (1–5) for each inference. The poster paper
and our other supplementary materials are available on
[OSF](https://osf.io/3enug/overview?view_only=25fe8c7e3d064e2ba722912ceccdfd39).

We are sharing these data in response to questions raised at the poster session:

- **Are gender and height inferences correlated?** Yes. Across clips, the
  proportion of observers who inferred a subject to be male is positively
  correlated with the clip's mean inferred height (upper body: r = .59,
  p = .010; full body: r = .69, p = .001), even though true height was largely
  decoupled from gender in our stimulus set (true difference 4.2 cm).
  See `analysis/`.
- **How could observers infer height above chance from height-normalized
  recordings?** Every model was uniformly scaled to the same size (see
  *Stimulus rendering*), so absolute body size was not available. The
  gender–height association above suggests that observers partly inferred
  height from the gender they perceived. The per-clip response distributions
  in `ratings_per_clip.csv` allow further exploration.

**Included:** aggregate participant demographics, per-clip response
distributions, accuracy and confidence for every clip × condition ×
attribute, the stimulus manifest, the gender–height analysis, figures, and
the scripts that generated them.

**Not included:** trial-level responses (our IRB approval permits sharing
aggregate results only), the rendered videos, and joint time series. The
videos and joint data are derived from the Nymeria dataset and can be
obtained from the source (see `stimuli_manifest.csv`).

---

## Files

### `demographics_aggregate.csv`
Participant demographics by condition (`upper_body` / `full_body`) for age,
gender, ethnicity, and motion-capture experience, as counts and percentages.
Participants who selected more than one ethnicity are grouped as
`multiracial`. No participant-level records, IDs, or timestamps are included.

Columns: `condition`, `attribute`, `category`, `n`, `percent`, `total_n`

### `ratings_per_clip.csv`
Aggregated observer responses for each clip, condition, and attribute
(18 clips × 2 conditions × 5 attributes = 180 rows). Each row reports:
- `ground_truth` — the subject's true value for that attribute
- `n_responses` — number of observer inferences (60, or 59 for a few clips)
- `accuracy` — proportion of correct inferences
- `response_counts` — JSON object: response category → count
- `response_pct` — JSON object: response category → percentage
- `mean_confidence` / `sd_confidence` — mean and SD of the 1–5 confidence rating

No participant-level records, IDs, or timestamps are included.

### `stimuli_manifest.csv`
One row per stimulus clip (18 clips); each clip was shown in both conditions.
- `clip_id` — filename used in the study (e.g., `alan_burns_5_20.mp4`)
- `nymeria_sequence_id` — the subject name used in Nymeria's file naming.
  These names are pseudonyms assigned by Nymeria, not the subjects' real
  names, so they do not identify anyone (and they do not indicate gender).
- `start_sec` / `end_sec` / `duration_sec` — segment within the Nymeria
  recording (15 s for all clips)
- `conditions` — always `upper_body,full_body`
- `ground_truth_gender/age_group/height_cm/weight_kg/ethnicity` — the
  subject's attributes from the Nymeria metadata
- `height_normalization` — `uniform_scale_max_dim_1.8` (see below)

Source: Nymeria dataset (L. Ma et al., ECCV 2024;
https://github.com/facebookresearch/nymeria_dataset), CC BY-NC 4.0.

### Stimulus rendering
The rendering method is described here and in the paper (Methods; Appendix B).
- **Source:** Nymeria Xsens motion capture (`.glb`), loaded with Three.js
  (r128) GLTFLoader and rendered as skeleton-only animation (no body mesh).
- **Segment:** 15 s per clip, starting at `start_sec`, with a fixed
  third-person camera that follows the subject.
- **Height normalisation:** each model is uniformly scaled so that its maximum
  bounding-box dimension equals 1.8 scene units
  (`scale = 1.8 / max(size.x, size.y, size.z)`). Scaling is applied at render
  time only.
- **Upper-body condition:** lower-body bones are hidden; the full list of
  included and excluded bones is given in Appendix B of the paper.

### `analysis/gender_height_clip_level.csv`
For each clip × condition: the proportion of observers who inferred the
subject to be male, and the mean inferred height, with each chosen height bin
coded at its midpoint (e.g., 170–180 cm → 175 cm).

Columns: `clip_id`, `nymeria_sequence_id`, `condition`, `n`,
`prop_guessed_male`, `mean_height_response_midpoint_cm`

### `analysis/gender_height_correlation_results.csv`
Pearson r between `prop_guessed_male` and `mean_height_response_midpoint_cm`
across clips (n = 18 clips per condition; two-tailed test of r = 0, df = 16).
- Upper-body condition: r = 0.587, t(16) = 2.90, p = .010
- Full-body condition:  r = 0.692, t(16) = 3.84, p = .001

This is a clip-level correlation: it shows that gender and height inferences
move together, not the order in which observers made them.

### `figures/`
- `fig1_demographics.png` — participant demographics by condition
  (from `demographics_aggregate.csv`)
- `fig2_accuracy_heatmap.png` — accuracy for each clip × attribute, by
  condition; each attribute is labelled with its chance level (gender .50,
  age .17, height .22, weight .18, ethnicity .28), so colours should be
  compared within, not across, attributes
- `fig3_confidence_heatmap.png` — mean confidence (1–5) for each clip ×
  attribute, by condition

### Scripts
- `build_osf_supplement.py` — generates all CSVs in this package. Provided
  for transparency; it reads the trial-level data, which is not shared, so
  it cannot be run from this package alone.
- `build_figures.py` — generates the figures from the CSVs in this package.

---

## Citation

If you use these materials, please cite our paper:

```bibtex
@inproceedings{liu2026fullbody,
  title     = {Does Full-Body Motion Reveal More? Comparing Human Inference of Personal Attributes from Upper-Body and Full-Body Motion},
  author    = {Liu, Jiayi and Wang, Arran Zeyu and Miller, Mark Roman and Szafir, Danielle and Payne, William},
  booktitle = {2026 IEEE International Symposium on Mixed and Augmented Reality Adjunct (ISMAR-Adjunct)},
  year      = {2026}
}
```
