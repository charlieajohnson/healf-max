---
id: oura_wearables
type: wearable_signal
title: Oura wearable recovery signals
status: active
pillar:
- sleep
- move
- mind
tags:
- oura
- deep_sleep
- hrv
- readiness
- recovery
- resting_heart_rate
signals:
- deep_sleep
- hrv
- readiness
- resting_heart_rate
routing:
  low_deep_sleep:
  - sleep_hygiene
  - magnesium_glycinate
  - caffeine_timing
  - wind_down
  below_baseline_hrv:
  - deprioritise_hard_training
  - recovery
  - protein
  - electrolytes
  low_readiness:
  - rest_or_easy_day
  - recovery
interpretation_guardrails:
- One night means little; read trends over one to two weeks.
- Wearable sleep stages are estimates, not lab sleep-study results.
- Wearable signals route attention; they do not diagnose.
wearable_correlates:
- low_deep_sleep
- below_baseline_hrv
- elevated_resting_heart_rate
source_path: supplied/scaffold/kb/signals/oura-wearables.md
source_notes:
- Oura Readiness Score uses recent activity, sleep patterns, resting heart rate, HRV and body temperature.
- Oura readiness ranges are 85+ optimal, 70-84 good, and under 70 pay attention.
retrieval_priority: 9
summary: Use Oura trends as a recovery compass, especially when low deep sleep or
  below-baseline HRV appears during a hard training block.
safety_boundary:
- no_diagnosis
- wearable_trends_are_estimates
- no_product_guarantees
prohibited_claims:
- diagnoses_sleep_disorder
- product_raises_hrv
- guaranteed_deep_sleep
reviewed_at: '2026-07-01'
---
# Summary

Oura and similar wearables are useful as a compass, not a verdict. Low deep sleep, below-baseline HRV, low readiness and elevated resting heart rate can point to recovery pressure, but they do not diagnose a sleep disorder or prove a supplement need.

# Routing

Low deep sleep routes to wind-down habits, caffeine timing and a modest sleep-support lane such as magnesium glycinate when appropriate. Below-baseline HRV during a hard training block routes first to reduced training load, sleep, protein and hydration.

# Answer boundary

Read trends over one to two weeks. Avoid overreacting to one night. Keep the language practical: let the data be useful without letting it become your personality.
