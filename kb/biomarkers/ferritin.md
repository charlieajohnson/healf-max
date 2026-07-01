---
id: ferritin
type: biomarker
title: Ferritin
status: active
pillar:
- eat
- move
tags:
- iron_status
- fatigue
- training
- recovery
- hyrox
aliases:
- serum_ferritin
- iron_stores
marker_unit: ng_ml
units: ng/mL equivalent to ug/L
bands:
  low: "<15 = iron deficiency threshold in many references; <30 = depleted stores context"
  suboptimal: "30-40 = often normal on a lab sheet but worth context in endurance fatigue"
  athlete_context: "40-90 = commonly discussed target context for active endurance customers"
  high: ">200-300 = investigate inflammation or iron overload context"
demo_result:
  value: 18
  status: low
interpretation_mode: plain_language
action_mode: clinician_follow_up
routes_to_goals:
- energy
- endurance_performance
- recovery
related_symptoms_or_goals:
- fatigue
- training_recovery
- exercise_tolerance
related_markers:
- haemoglobin
- transferrin_saturation
- b12
evidence_routes:
- ferritin_low_fatigue
- bloods_plain_language
product_lanes:
- iron_support
- bloods_testing
- expert_advice
ingredient_lanes:
- iron
- vitamin_c
wearable_correlates:
- low_energy
- poor_recovery
- elevated_resting_heart_rate
population_risk:
- menstruating
- plant_based
- vegetarian
- vegan
- endurance_training
escalation_mode: abnormal_bloods_need_follow_up
follow_up_language: Low ferritin is worth GP, clinician or practitioner review before
  supplementing, especially with fatigue or heavy training.
source_path: supplied/scaffold/kb/biomarkers/ferritin.md
source_notes:
- NIH ODS Iron describes iron as part of haemoglobin and myoglobin, supporting oxygen transport and muscle metabolism.
- NIH ODS notes calcium and iron supplements are often taken at different times because of absorption interference.
retrieval_priority: 10
safety_boundary:
- abnormal_bloods_need_follow_up
- no_diagnosis
- no_dosing
prohibited_claims:
- diagnosis
- product_as_treatment
- specific_dosing_for_abnormal_result
- treats_anaemia
- cures_fatigue
reviewed_at: '2026-07-01'
---
# Summary

Ferritin reflects iron stores. It can fall before haemoglobin changes, so it is useful context for tiredness and training tolerance, especially in plant-based, menstruating or endurance-training customers.

# Plain-language route

Explain ferritin as the body's iron savings account. Low or borderline ferritin with fatigue is a follow-up moment before product certainty. It can help explain why an endurance customer feels flat, but it does not prove one cause.

# Endurance and plant-based context

Endurance training can raise iron demand, and plant-based diets rely on non-haem iron. If the customer is training hard, tired and plant-based, route to ferritin plus B12 context early.

# Product boundary

Iron support is a contextual lane only after bloods and appropriate guidance. Keep timing advice high-level and do not provide dosing for a flagged result.
