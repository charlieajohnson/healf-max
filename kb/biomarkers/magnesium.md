---
id: magnesium
type: biomarker
title: Magnesium
status: active
pillar:
- sleep
- mind
- move
tags:
- magnesium
- sleep
- deep_sleep
- recovery
aliases:
- serum_magnesium
marker_unit: mmol_l
units: mmol/L
bands:
  low: "<0.75 mmol/L is hypomagnesaemia context in NIH ODS material"
  suboptimal: "0.75-0.80 can still need context because serum is a weak whole-body marker"
  normal: "0.75-0.95 is a common serum reference context"
  high: ">1.0 should be reviewed, especially with kidney context"
demo_result:
  value: suboptimal
  status: suboptimal
interpretation_mode: plain_language
action_mode: wellness_plus_follow_up
routes_to_goals:
- sleep_quality
- recovery
- stress
related_symptoms_or_goals:
- low_deep_sleep
- recovery_bottleneck
related_markers:
- vitamin_d
- calcium
evidence_routes:
- magnesium_sleep_recovery
- bloods_plain_language
product_lanes:
- magnesium_glycinate
- bloods_testing
ingredient_lanes:
- magnesium_glycinate
- magnesium_l_threonate
- magnesium_malate
wearable_correlates:
- low_deep_sleep
- below_baseline_hrv
escalation_mode: check_context
follow_up_language: Generally well tolerated, but caution with kidney disease,
  high doses, laxative effects and relevant medicines.
source_path: supplied/scaffold/kb/biomarkers/magnesium.md
source_notes:
- NIH ODS describes magnesium as a cofactor in more than 300 enzyme systems, including muscle and nerve function.
- NIH ODS says serum magnesium is common but does not accurately reflect total body magnesium.
retrieval_priority: 8
safety_boundary:
- abnormal_bloods_need_follow_up
- no_diagnosis
- no_dosing
prohibited_claims:
- diagnosis
- product_as_treatment
- specific_dosing_for_abnormal_result
- treats_insomnia
- cures_anxiety
- guarantees_deep_sleep
reviewed_at: '2026-07-01'
---
# Summary

Magnesium is a workhorse mineral for muscle, nerve and energy processes. It is also a common customer route around sleep and recovery, but serum magnesium is an imperfect status marker.

# Plain-language route

Explain that a normal serum result does not capture the whole picture, so the answer should lean on the customer's sleep/recovery goal and safety context rather than the number alone.

# Wearable route

Low deep sleep or below-baseline HRV can support a magnesium sleep lane alongside wind-down habits and training-load review. Keep the claim modest: it may support sleep quality, but it does not guarantee deep sleep.

# Product boundary

Product lanes are contextual support only. Flagged blood results should not become product certainty.
