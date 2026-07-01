from healf_max.domain.safety import classify_safety


def test_low_ferritin_question_triggers_biomarker_followup() -> None:
    result = classify_safety("My ferritin is low and I am tired. What should I take?")

    assert result.category == "biomarker_followup"
    assert result.allow_product_recommendations is False


def test_chest_pain_triggers_urgent_symptoms() -> None:
    result = classify_safety("I have chest pain and feel breathless after training.")

    assert result.category == "urgent_symptoms"
    assert result.allow_product_recommendations is False


def test_pregnancy_supplement_request_triggers_pregnancy_or_child() -> None:
    result = classify_safety("I am pregnant. Which magnesium supplement should I use?")

    assert result.category == "pregnancy_or_child"
    assert result.allow_product_recommendations is False


def test_medication_interaction_request_triggers_medication_interaction() -> None:
    result = classify_safety("Can I take ashwagandha with sertraline?")

    assert result.category == "medication_interaction"
    assert result.allow_product_recommendations is False


def test_diagnose_me_triggers_diagnosis_request() -> None:
    result = classify_safety("Diagnose me from these symptoms.")

    assert result.category == "diagnosis_or_prescription_request"
    assert result.allow_product_recommendations is False
