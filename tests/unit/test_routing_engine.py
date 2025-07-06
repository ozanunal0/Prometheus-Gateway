"""
Unit tests for the intelligent routing engine.

Tests the provider factory, model-to-provider mapping, and configuration-driven
routing logic without making actual API calls.
"""

import pytest
from unittest.mock import patch, Mock
import os

from app.services import get_provider
from app.config import Config, ProviderConfig
from app.providers.openai.provider import OpenAIProvider
from app.providers.google.provider import GoogleProvider
from app.providers.anthropic.provider import AnthropicProvider


@pytest.mark.unit
@pytest.mark.routing
class TestRoutingEngine:
    """Test suite for the intelligent routing engine."""

    def test_get_provider_openai_models(self, test_config, mock_env_vars):
        """Test routing for OpenAI models."""
        with patch('app.services.config', test_config):
            # Test all OpenAI models
            for model in ["gpt-4o", "gpt-3.5-turbo"]:
                provider = get_provider(model)
                assert isinstance(provider, OpenAIProvider)
                assert provider.api_key == "test-openai-key-123"

    def test_get_provider_google_models(self, test_config, mock_env_vars):
        """Test routing for Google models."""
        with patch('app.services.config', test_config):
            # Test all Google models
            for model in ["gemini-2.5-flash", "gemini-2.5-pro"]:
                with patch('google.generativeai.configure'):
                    provider = get_provider(model)
                    assert isinstance(provider, GoogleProvider)
                    assert provider.api_key == "test-google-key-456"

    def test_get_provider_anthropic_models(self, test_config, mock_env_vars):
        """Test routing for Anthropic models."""
        with patch('app.services.config', test_config):
            # Test all Anthropic models
            for model in ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]:
                with patch('anthropic.AsyncAnthropic'):
                    provider = get_provider(model)
                    assert isinstance(provider, AnthropicProvider)
                    assert provider.api_key == "test-anthropic-key-789"

    def test_get_provider_unsupported_model(self, test_config):
        """Test error handling for unsupported models."""
        with patch('app.services.config', test_config):
            with pytest.raises(ValueError) as exc_info:
                get_provider("unsupported-model-123")
            
            assert "No provider found for model: unsupported-model-123" in str(exc_info.value)

    def test_get_provider_missing_api_key(self, test_config):
        """Test error handling when API key environment variable is missing."""
        # Create config with missing env var
        providers = [
            ProviderConfig(
                name="openai",
                api_key_env="MISSING_API_KEY",
                models=["gpt-3.5-turbo"]
            )
        ]
        config_with_missing_key = Config(providers=providers)
        
        with patch('app.services.config', config_with_missing_key):
            with pytest.raises(ValueError) as exc_info:
                get_provider("gpt-3.5-turbo")
            
            assert "Environment variable MISSING_API_KEY not set" in str(exc_info.value)

    def test_config_driven_routing_priority(self, mock_env_vars):
        """Test that routing follows configuration order."""
        # Create config where the same model is in multiple providers
        providers = [
            ProviderConfig(
                name="openai", 
                api_key_env="TEST_OPENAI_API_KEY",
                models=["shared-model"]
            ),
            ProviderConfig(
                name="google",
                api_key_env="TEST_GOOGLE_API_KEY", 
                models=["shared-model"]
            )
        ]
        config_with_duplicate = Config(providers=providers)
        
        with patch('app.services.config', config_with_duplicate):
            # Should return the first provider that matches
            provider = get_provider("shared-model")
            assert isinstance(provider, OpenAIProvider)

    def test_model_case_sensitivity(self, test_config, mock_env_vars):
        """Test that model matching is case-sensitive."""
        with patch('app.services.config', test_config):
            # Should work with exact case
            provider = get_provider("gpt-4o")
            assert isinstance(provider, OpenAIProvider)
            
            # Should fail with different case
            with pytest.raises(ValueError):
                get_provider("GPT-4O")
            
            with pytest.raises(ValueError):
                get_provider("gpt-4O")

    def test_empty_configuration(self):
        """Test behavior with empty provider configuration."""
        empty_config = Config(providers=[])
        
        with patch('app.services.config', empty_config):
            with pytest.raises(ValueError) as exc_info:
                get_provider("any-model")
            
            assert "No provider found for model: any-model" in str(exc_info.value)

    def test_provider_with_no_models(self, mock_env_vars):
        """Test provider configuration with empty models list."""
        providers = [
            ProviderConfig(
                name="openai",
                api_key_env="TEST_OPENAI_API_KEY",
                models=[]  # Empty models list
            )
        ]
        config_no_models = Config(providers=providers)
        
        with patch('app.services.config', config_no_models):
            with pytest.raises(ValueError):
                get_provider("gpt-3.5-turbo")

    def test_dynamic_configuration_reload(self, mock_env_vars):
        """Test that routing adapts to configuration changes."""
        # Start with OpenAI only
        initial_config = Config(providers=[
            ProviderConfig(
                name="openai",
                api_key_env="TEST_OPENAI_API_KEY",
                models=["gpt-3.5-turbo"]
            )
        ])
        
        # Add Google provider
        updated_config = Config(providers=[
            ProviderConfig(
                name="openai",
                api_key_env="TEST_OPENAI_API_KEY",
                models=["gpt-3.5-turbo"]
            ),
            ProviderConfig(
                name="google",
                api_key_env="TEST_GOOGLE_API_KEY",
                models=["gemini-2.5-flash"]
            )
        ])
        
        # Test with initial config
        with patch('app.services.config', initial_config):
            provider = get_provider("gpt-3.5-turbo")
            assert isinstance(provider, OpenAIProvider)
            
            with pytest.raises(ValueError):
                get_provider("gemini-2.5-flash")
        
        # Test with updated config
        with patch('app.services.config', updated_config):
            with patch('google.generativeai.configure'):
                provider = get_provider("gemini-2.5-flash")
                assert isinstance(provider, GoogleProvider)

    def test_special_characters_in_model_names(self, mock_env_vars):
        """Test handling of model names with special characters."""
        providers = [
            ProviderConfig(
                name="openai",
                api_key_env="TEST_OPENAI_API_KEY",
                models=["model-with-dashes", "model_with_underscores", "model.with.dots"]
            )
        ]
        config_special_chars = Config(providers=providers)
        
        with patch('app.services.config', config_special_chars):
            for model in ["model-with-dashes", "model_with_underscores", "model.with.dots"]:
                provider = get_provider(model)
                assert isinstance(provider, OpenAIProvider)

    def test_provider_instantiation_isolation(self, test_config, mock_env_vars):
        """Test that each provider call creates a new instance."""
        with patch('app.services.config', test_config):
            provider1 = get_provider("gpt-3.5-turbo")
            provider2 = get_provider("gpt-3.5-turbo")
            
            # Should be different instances
            assert provider1 is not provider2
            # But should have the same API key
            assert provider1.api_key == provider2.api_key

    def test_routing_performance_with_many_providers(self, mock_env_vars):
        """Test routing performance with a large number of providers."""
        # Create many providers with many models each
        providers = []
        for i in range(10):
            models = [f"model-{i}-{j}" for j in range(20)]
            providers.append(ProviderConfig(
                name="openai",
                api_key_env="TEST_OPENAI_API_KEY",
                models=models
            ))
        
        large_config = Config(providers=providers)
        
        with patch('app.services.config', large_config):
            # Should still find the model efficiently
            provider = get_provider("model-5-10")
            assert isinstance(provider, OpenAIProvider)
            
            # Should still handle unknown models
            with pytest.raises(ValueError):
                get_provider("unknown-model")

    def test_provider_factory_extensibility(self, mock_env_vars):
        """Test that the factory can be extended with new providers."""
        # This test simulates adding a new provider type
        providers = [
            ProviderConfig(
                name="future_provider",  # New provider type
                api_key_env="TEST_FUTURE_API_KEY",
                models=["future-model-1"]
            )
        ]
        future_config = Config(providers=providers)
        
        # Set the future API key
        os.environ["TEST_FUTURE_API_KEY"] = "test-future-key"
        
        with patch('app.services.config', future_config):
            # Should raise ValueError for unknown provider type
            with pytest.raises(ValueError):
                get_provider("future-model-1")
        
        # Cleanup
        os.environ.pop("TEST_FUTURE_API_KEY", None)