import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from modules.quality_evaluation.schemas import QualityEvaluationRequest
from modules.quality_evaluation.service import QualityEvaluationService


def payload():
    return json.loads((Path(__file__).parent / 'fixtures/module_outputs/requirements-request.json').read_text())


def test_analysis_output_is_split_and_metadata_excluded():
    raw = payload()
    model = QualityEvaluationRequest.model_validate(raw)
    assert len(model.functional_requirements) == 2
    assert len(model.non_functional_requirements) == 2
    assert model.functional_requirements[0].statement == raw['requirement_analysis']['requirements'][0]['normalized_statement']
    assert model.non_functional_requirements[0].category == 'Security'
    assert model.functional_requirements[0].priority is None
    saved = model.model_dump(mode='json')
    assert 'requirement_analysis' not in saved
    assert 'generated_srs' not in str(saved)
    assert QualityEvaluationRequest.model_validate(saved).model_dump() == saved
    result = QualityEvaluationService(enable_llm=False).evaluate(model)
    assert {'SEC-002', 'SCAL-001'} <= set(result.applicable_rule_ids)


@pytest.mark.parametrize('category', [None, 'Reliability', 'Unknown'])
def test_missing_or_unsupported_category_is_not_guessed(category):
    raw = payload()
    raw['requirement_analysis']['requirements'][2]['quality_attribute'] = category
    with pytest.raises(ValidationError, match='NFR quality_attribute must be a supported category'):
        QualityEvaluationRequest.model_validate(raw)


def test_analysis_project_must_match():
    raw = payload()
    raw['requirement_analysis']['project_id'] = 'another-project'
    with pytest.raises(ValidationError, match='requirement_analysis.project_id must match'):
        QualityEvaluationRequest.model_validate(raw)


def test_conflicting_sources_rejected():
    raw = payload()
    raw['functional_requirements'] = []
    with pytest.raises(ValidationError, match='conflicting requirement sources'):
        QualityEvaluationRequest.model_validate(raw)


def test_duplicate_requirement_ids_rejected():
    raw = payload()
    raw['requirement_analysis']['requirements'][1]['requirement_id'] = 'FR-001'
    with pytest.raises(ValidationError, match='Duplicate analyzed requirement ID'):
        QualityEvaluationRequest.model_validate(raw)


def test_blank_normalized_text_rejected():
    raw = payload()
    raw['requirement_analysis']['requirements'][0]['normalized_statement'] = ' '
    with pytest.raises(ValidationError, match='non-empty'):
        QualityEvaluationRequest.model_validate(raw)
