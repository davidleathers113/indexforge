"""Shared fixtures for summarizer tests."""

from unittest.mock import MagicMock

import pytest
import torch
from transformers import PretrainedConfig


class MockConfig(PretrainedConfig):
    """Mock config for testing."""

    def __init__(self):
        super().__init__()
        # Required attributes for BART
        self._commit_hash = "mock-hash"
        self.architectures = ["BartForConditionalGeneration"]
        self.model_type = "bart"
        self.vocab_size = 50265  # Standard BART vocab size
        self.max_position_embeddings = 1024
        self.encoder_layers = 1
        self.encoder_attention_heads = 1
        self.decoder_layers = 1
        self.decoder_attention_heads = 1
        self.encoder_ffn_dim = 128
        self.decoder_ffn_dim = 128
        self.d_model = 64
        self.pad_token_id = 1
        self.bos_token_id = 0
        self.eos_token_id = 2
        self.is_encoder_decoder = True
        self.decoder_start_token_id = 2
        self.forced_eos_token_id = 2
        self.dropout = 0.1
        self.attention_dropout = 0.1
        self.activation_dropout = 0.1
        self.classifier_dropout = 0.0
        self.scale_embedding = True
        self.normalize_before = False
        self.activation_function = "gelu"
        self.num_hidden_layers = 1
        # BART-specific attributes
        self.encoder_layerdrop = 0.0
        self.decoder_layerdrop = 0.0
        self.use_cache = True
        self.num_labels = 3
        self.init_std = 0.02
        self.output_past = True
        self.return_dict = True


class MockModel(torch.nn.Module):
    """Mock model for testing."""

    def __init__(self):
        super().__init__()
        self.config = MockConfig()
        # Add BART-specific attributes that the pipeline might check
        self.name_or_path = "facebook/bart-large-cnn"
        self.generation_config = MagicMock()
        self.main_input_name = "input_ids"

    def forward(self, *args, **kwargs):
        """Mock forward pass."""
        # Return a tensor that looks like a valid output
        return {"logits": torch.tensor([[1.0]])}

    def eval(self):
        """Mock eval mode."""
        return self

    def to(self, device):
        """Mock device movement."""
        return self


class MockTFModel:
    """Mock TensorFlow model for testing."""

    def __init__(self):
        self.config = MockConfig()
        # Add BART-specific attributes that the pipeline might check
        self.name_or_path = "facebook/bart-large-cnn"
        self.generation_config = MagicMock()
        self.main_input_name = "input_ids"

    def __call__(self, *args, **kwargs):
        """Mock forward pass."""
        # Return a tensor that looks like a valid output
        return {"logits": torch.tensor([[1.0]])}


@pytest.fixture
def mock_summarizer_setup(mocker):
    """Set up mocks for summarizer tests."""
    mock_pipeline = mocker.patch("transformers.pipeline")
    mock_pipeline_instance = mocker.Mock()

    def mock_summarize(*args, **kwargs):
        # If side_effect is set, raise the error
        if mock_pipeline_instance.side_effect is not None:
            if isinstance(mock_pipeline_instance.side_effect, Exception):
                raise mock_pipeline_instance.side_effect
            return mock_pipeline_instance.side_effect(*args, **kwargs)

        # Generate a summary that meets the length requirements
        min_length = kwargs.get("min_length", 30)
        max_length = kwargs.get("max_length", 130)
        summary = "Mocked " + "summary " * ((min_length // 7) + 1)
        summary = summary[:max_length]  # Truncate to max_length
        return [{"summary_text": summary.strip()}]

    # Set up the mock pipeline instance to use the mock_summarize function
    mock_pipeline_instance.side_effect = None
    mock_pipeline_instance.__call__ = mock_summarize
    mock_pipeline_instance.return_value = mock_pipeline_instance

    # Set up the pipeline mock to return our instance
    mock_pipeline.return_value = mock_pipeline_instance

    return {
        "pipeline": mock_pipeline,
        "pipeline_instance": mock_pipeline_instance,
    }


@pytest.fixture
def mock_tf_summarizer_setup(mocker):
    """Set up all mocks needed for TensorFlow summarizer tests."""
    # Mock the config to prevent loading from Hugging Face Hub
    mock_config = MockConfig()
    mocker.patch("transformers.AutoConfig.from_pretrained", return_value=mock_config)

    # Create a mock model that will be recognized as a TF model
    mock_model = MockTFModel()
    mocker.patch("transformers.TFAutoModelForSeq2SeqLM.from_pretrained", return_value=mock_model)

    # Mock the tokenizer
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token_id = mock_config.pad_token_id
    mock_tokenizer.bos_token_id = mock_config.bos_token_id
    mock_tokenizer.eos_token_id = mock_config.eos_token_id
    mocker.patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer)

    # Mock the pipeline function
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.return_value = [{"summary_text": "TF mocked summary"}]

    # Create a callable mock that returns itself
    def mock_call(*args, **kwargs):
        return [{"summary_text": "TF mocked summary"}]

    mock_pipeline_instance.side_effect = mock_call

    def mock_pipeline(task, model=None, device=None, **kwargs):
        if task == "summarization":
            return mock_pipeline_instance
        raise ValueError(f"Unsupported task: {task}")

    pipeline_mock = mocker.patch("transformers.pipeline", side_effect=mock_pipeline)

    return {
        "model": mock_model,
        "tokenizer": mock_tokenizer,
        "pipeline": pipeline_mock,
        "pipeline_instance": mock_pipeline_instance,
        "config": mock_config,
    }


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache_manager = MagicMock()
    cache_manager.get.return_value = None
    return cache_manager
