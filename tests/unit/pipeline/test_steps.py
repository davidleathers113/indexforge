from src.pipeline.steps import PipelineStep

def test_pipeline_steps_uniqueness():
    """Test that all pipeline steps have unique values"""
    values = [step.value for step in PipelineStep]
    assert len(values) == len(set(values)), 'Pipeline steps should have unique values'

def test_pipeline_steps_completeness():
    """Test that all expected pipeline steps are present"""
    expected_steps = {'LOAD', 'DEDUPLICATE', 'PII', 'SUMMARIZE', 'EMBED', 'CLUSTER', 'INDEX'}
    actual_steps = {step.name for step in PipelineStep}
    assert actual_steps == expected_steps, 'Missing or unexpected pipeline steps'

def test_pipeline_step_membership():
    """Test that membership testing works correctly"""
    assert PipelineStep.LOAD in set(PipelineStep)
    assert 'NOT_A_STEP' not in {step.name for step in PipelineStep}

def test_pipeline_step_comparison():
    """Test that pipeline steps can be compared correctly"""
    assert PipelineStep.LOAD == PipelineStep.LOAD
    assert PipelineStep.LOAD != PipelineStep.INDEX
    assert PipelineStep.LOAD != 'LOAD'

def test_pipeline_step_iteration():
    """Test that pipeline steps can be iterated over"""
    steps = list(PipelineStep)
    assert len(steps) == 7
    assert all((isinstance(step, PipelineStep) for step in steps))

def test_pipeline_step_string_representation():
    """Test string representation of pipeline steps"""
    assert str(PipelineStep.LOAD) == 'PipelineStep.LOAD'
    assert repr(PipelineStep.LOAD) == 'PipelineStep.LOAD'

def test_pipeline_step_value_assignment():
    """Test that auto() assigns incrementing values"""
    steps = list(PipelineStep)
    values = [step.value for step in steps]
    assert all((isinstance(value, int) for value in values))
    assert values == sorted(values)
    assert len(set(values)) == len(values)