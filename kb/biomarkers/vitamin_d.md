---
id: vitamin_d
type: biomarker
title: Vitamin D
status: active
pillar:
- eat
- move
tags:
- vitamin_d
- general_health
- musculoskeletal
- bloods
aliases:
- 25_hydroxyvitamin_d
- 25_oh_d
marker_unit: nmol_l
units: nmol/L
bands:
  low: "<25 nmol/L is UK deficiency context"
  insufficient: "25-50 nmol/L can be insufficient for some people"
  sufficient: "50+ nmol/L is sufficient for most people"
  high: ">125 nmol/L should be reviewed; avoid very high supplemental intakes"
demo_result:
  value: 42
  status: low
interpretation_mode: plain_language
action_mode: practitioner_guided
routes_to_goals:
- energy
- immunity
- mood
- bone_and_muscle
related_symptoms_or_goals:
- low_mood_winter
- bone_muscle_support
- general_health
related_markers:
- calcium
- pth
evidence_routes:
- vitamin_d_low_status
- bloods_plain_language
product_lanes:
- vitamin_d_contextual
- bloods_testing
- expert_advice
escalation_mode: practitioner_guided
follow_up_language: Deficient vitamin D is worth a clinician conversation for
  dosing. General UK advice is 10 micrograms daily in autumn and winter.
source_path: supplied/scaffold/kb/biomarkers/vitamin-d.md
source_notes:
- NHS says adults and children over 4 need 10 micrograms vitamin D daily.
- NHS says people should consider 10 micrograms daily in autumn and winter, and avoid more than 100 micrograms daily unless advised.
retrieval_priority: 8
safety_boundary:
- abnormal_bloods_need_follow_up
- no_diagnosis
- no_dosing
prohibited_claims:
- diagnosis
- product_as_treatment
- specific_dosing_for_abnormal_result
- treats_depression
- cures_fatigue
- prevents_illness
reviewed_at: '2026-07-01'
---
# Summary

Vitamin D status gives useful context for bone, muscle and general wellbeing support. In the UK it is especially seasonal because sunlight is limited in autumn and winter.

# Plain-language route

Explain vitamin D as the sunshine marker. If the result is deficient, lead with follow-up and safe dosing guidance from a clinician. If the customer is asking generally, mention the UK autumn/winter 10 microgram guidance as general public-health context.

# Product boundary

Product lanes are contextual support only. Flagged blood results should not become product certainty.
