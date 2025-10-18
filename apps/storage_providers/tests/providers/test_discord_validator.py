"""
Unit tests for DiscordConfigValidator.
"""
import pytest
from apps.storage_providers.providers.discord.discord_validator import DiscordConfigValidator


class TestDiscordConfigValidatorSchema:
    """Tests for schema validation (required fields, types)."""
    
    def test_valid_config_passes(self):
        """Test that a valid config passes validation."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is True
        assert len(validator.get_errors()) == 0
    
    def test_missing_bot_token_fails(self):
        """Test that missing bot_token fails validation."""
        config = {
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('bot_token' in error for error in validator.get_errors())
    
    def test_missing_server_id_fails(self):
        """Test that missing server_id fails validation."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('server_id' in error for error in validator.get_errors())
    
    def test_missing_channel_id_fails(self):
        """Test that missing channel_id fails validation."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('channel_id' in error for error in validator.get_errors())
    
    def test_empty_bot_token_fails(self):
        """Test that empty bot_token fails validation."""
        config = {
            'bot_token': '',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('bot_token' in error and 'empty' in error.lower() for error in validator.get_errors())
    
    def test_none_values_fail(self):
        """Test that None values fail validation."""
        config = {
            'bot_token': None,
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('bot_token' in error for error in validator.get_errors())
    
    def test_wrong_type_bot_token_fails(self):
        """Test that wrong type for bot_token fails validation."""
        config = {
            'bot_token': 12345,  # Should be string
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('bot_token' in error and 'str' in error for error in validator.get_errors())
    
    def test_server_id_accepts_string(self):
        """Test that server_id accepts string type."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is True
    
    def test_server_id_accepts_int(self):
        """Test that server_id accepts int type."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': 123456789012345678,
            'channel_id': 987654321098765432,
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is True
    
    def test_non_dict_config_fails(self):
        """Test that non-dict config fails validation."""
        config = "not a dict"
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('dictionary' in error.lower() for error in validator.get_errors())


class TestDiscordConfigValidatorFormats:
    """Tests for format validation (patterns, IDs)."""
    
    def test_valid_bot_token_format_passes(self):
        """Test that valid bot token format passes without warnings."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        assert len(validator.get_warnings()) == 0
    
    def test_invalid_bot_token_format_warns(self):
        """Test that invalid bot token format triggers warning."""
        config = {
            'bot_token': 'invalid-token',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        assert any('token' in warning.lower() for warning in validator.get_warnings())
    
    def test_valid_snowflake_ids_pass(self):
        """Test that valid Snowflake IDs pass validation."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',  # 18 digits
            'channel_id': '98765432109876543',  # 17 digits
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is True
    
    def test_short_snowflake_fails(self):
        """Test that too-short Snowflake ID fails validation."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123',  # Too short
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('server_id' in error and 'Snowflake' in error for error in validator.get_errors())
    
    def test_non_numeric_snowflake_fails(self):
        """Test that non-numeric Snowflake ID fails validation."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': 'not-a-number',
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True) is False
        assert any('channel_id' in error for error in validator.get_errors())


class TestDiscordConfigValidatorBusinessRules:
    """Tests for business logic validation (chunk sizes, limits)."""
    
    def test_default_chunk_size_passes(self):
        """Test that 8MB chunk size passes without warnings."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
            'max_chunk_size': 8 * 1024 * 1024,
        }
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        assert len(validator.get_warnings()) == 0
    
    def test_chunk_size_too_small_warns(self):
        """Test that too-small chunk size triggers warning."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
            'max_chunk_size': 100,  # Too small
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True)
        assert any('too small' in error.lower() for error in validator.get_warnings())

    def test_chunk_size_too_large_warns(self):
        """Test that too-large chunk size triggers warning."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
            'max_chunk_size': 100 * 1024 * 1024,  # 100MB - exceeds Discord limit
        }
        validator = DiscordConfigValidator(config)
        assert validator.validate(skip_api_check=True)
        assert any('exceeds' in error.lower() for error in validator.get_warnings())
    
    def test_chunk_size_above_recommended_warns(self):
        """Test that chunk size above recommended triggers warning."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
            'max_chunk_size': 9 * 1024 * 1024,  # 9MB - larger than recommended
        }
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        assert any('recommended' in warning.lower() for warning in validator.get_warnings())
    

class TestDiscordConfigValidatorHelpers:
    """Tests for helper methods."""
    
    def test_get_errors_returns_copy(self):
        """Test that get_errors returns a copy of errors list."""
        config = {'bot_token': 'invalid'}
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        
        errors1 = validator.get_errors()
        errors2 = validator.get_errors()
        
        assert errors1 == errors2
        assert errors1 is not errors2  # Different objects
    
    def test_get_warnings_returns_copy(self):
        """Test that get_warnings returns a copy of warnings list."""
        config = {
            'bot_token': 'short',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        
        warnings1 = validator.get_warnings()
        warnings2 = validator.get_warnings()
        
        assert warnings1 == warnings2
        assert warnings1 is not warnings2  # Different objects
    
    def test_get_validation_report_valid(self):
        """Test validation report for valid config."""
        config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        
        report = validator.get_validation_report()
        assert '✓' in report
        assert 'valid' in report.lower()
    
    def test_get_validation_report_with_errors(self):
        """Test validation report with errors."""
        config = {}
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        
        report = validator.get_validation_report()
        assert '✗' in report
        assert 'error' in report.lower()
        assert 'bot_token' in report
    
    def test_get_validation_report_with_warnings(self):
        """Test validation report with warnings."""
        config = {
            'bot_token': 'short',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator = DiscordConfigValidator(config)
        validator.validate(skip_api_check=True)
        
        report = validator.get_validation_report()
        assert '⚠' in report
        assert 'warning' in report.lower()
    
    def test_validation_clears_previous_errors(self):
        """Test that re-running validation clears previous errors."""
        config = {}
        validator = DiscordConfigValidator(config)
        
        # First validation - should fail
        validator.validate(skip_api_check=True)
        first_error_count = len(validator.get_errors())
        assert first_error_count > 0
        
        # Update config and validate again
        validator.config = {
            'bot_token': 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs',
            'server_id': '123456789012345678',
            'channel_id': '987654321098765432',
        }
        validator.validate(skip_api_check=True)
        
        # Should have no errors now
        assert len(validator.get_errors()) == 0
