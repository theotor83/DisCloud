import re
import logging
import httpx

logger = logging.getLogger(__name__)

class DiscordConfigValidator:
    """
    Validates Discord storage provider configuration.
    
    Performs multi-layer validation:
    1. Schema validation (required fields, types)
    2. Format validation (token patterns, ID formats)
    3. Business logic validation (size limits, etc.)
    4. Live API validation (check bot token works)
    
    Optional: Can perform live API validation (check bot token works)
    """
    
    # Format: MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ.ZnCjm1XVW7vRze4b7Cq4se7kKWs (example)
    BOT_TOKEN_PATTERN = re.compile(r'^[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{27,}$')
    
    # Discord Snowflake IDs are 17-19 digits typically
    SNOWFLAKE_PATTERN = re.compile(r'^\d{17,19}$')
    
    # Chunk size limits
    MIN_CHUNK_SIZE = 1024  # 1KB minimum
    MAX_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB (Discord free account limit)
    RECOMMENDED_MAX_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB recommended
    
    def __init__(self, config):
        self.config = config
        self.errors = []
        self.warnings = []

    def validate(self, allow_errors=False, skip_api_check=False) -> bool:
        """
        Validates the Discord configuration.
        
        Args:
            allow_errors: If True, returns True even if there are validation errors.
            skip_api_check: If True, skips live API validation (check bot token works).
            Should only be changed in test environments.

        Returns:
            bool: True if config is valid (or has only warnings), False otherwise.
        """
        self.errors = []
        self.warnings = []
        
        # Layer 1: Schema validation
        self._validate_schema()
        
        # Layer 2: Format validation (only if schema is valid)
        if not self.errors:
            self._validate_formats()
        
        # Layer 3: Business logic validation
        if not self.errors:
            self._validate_business_rules()

        # Layer 4: Live API validation
        if not self.errors and not skip_api_check:
            self._validate_live_api()

        # Log results
        if self.errors:
            for error in self.errors:
                logger.error(f"Discord config validation error: {error}")
        if self.warnings:
            for warning in self.warnings:
                logger.warning(f"Discord config validation warning: {warning}")

        logger.info(f"Discord config validation completed: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        logger.debug(self.get_validation_report())
        
        # Return validation result
        if not allow_errors:
            return len(self.errors) == 0
        else:
            logger.info(f"Validation completed with errors allowed; returning True even if {len(self.errors)} errors exist.")
            return True

    def _validate_schema(self):
        """Validates required fields exist and have correct types."""
        if not isinstance(self.config, dict):
            self.errors.append("Config must be a dictionary")
            return
        
        # Required fields
        required_fields = {
            'bot_token': str,
            'server_id': (str, int),  # Can be string or int
            'channel_id': (str, int),
        }
        
        for field, expected_type in required_fields.items():
            if field not in self.config:
                self.errors.append(f"Missing required field: '{field}'")
                continue
            
            value = self.config[field]
            
            # Check for empty values
            if value is None or value == '':
                self.errors.append(f"Field '{field}' cannot be empty")
                continue
            
            # Check type
            if not isinstance(value, expected_type):
                if isinstance(expected_type, tuple):
                    type_names = ' or '.join(t.__name__ for t in expected_type)
                    self.errors.append(
                        f"Field '{field}' must be {type_names}, got {type(value).__name__}"
                    )
                else:
                    self.errors.append(
                        f"Field '{field}' must be {expected_type.__name__}, got {type(value).__name__}"
                    )
        
        # Optional fields with type checking
        optional_fields = {
            'max_chunk_size': int,
        }
        
        for field, expected_type in optional_fields.items():
            if field in self.config:
                value = self.config[field]
                if value is not None and not isinstance(value, expected_type):
                    self.errors.append(
                        f"Optional field '{field}' must be {expected_type.__name__}, got {type(value).__name__}"
                    )

    def _validate_formats(self):
        """Validates field formats and patterns."""
        # Validate bot token format
        bot_token = str(self.config.get('bot_token', ''))
        if bot_token and not self.BOT_TOKEN_PATTERN.match(bot_token):
            self.warnings.append(
                "Bot token doesn't match expected Discord token format. "
                "This might be a test token or incorrectly formatted."
            )
        
        # Validate server and channel IDs
        for field in ['server_id', 'channel_id']:
            value = self.config.get(field)
            if value is not None:
                # Convert to string for pattern matching
                value_str = str(value)
                if not self.SNOWFLAKE_PATTERN.match(value_str):
                    self.errors.append(
                        f"'{field}' ({value_str}) doesn't match Discord Snowflake ID format (17-19 digits)"
                    )

    def _validate_business_rules(self):
        """Validates business logic and constraints."""
        # Validate chunk size
        max_chunk_size = self.config.get('max_chunk_size')
        if max_chunk_size is not None:
            if max_chunk_size < self.MIN_CHUNK_SIZE:
                self.warnings.append(
                    f"max_chunk_size ({max_chunk_size}) is too small. "
                    f"Minimum is {self.MIN_CHUNK_SIZE} bytes"
                )
            elif max_chunk_size > self.MAX_CHUNK_SIZE:
                self.warnings.append(
                    f"max_chunk_size ({max_chunk_size}) exceeds Discord's limit. "
                    f"Maximum is {self.MAX_CHUNK_SIZE} bytes"
                )
            elif max_chunk_size > self.RECOMMENDED_MAX_CHUNK_SIZE:
                self.warnings.append(
                    f"max_chunk_size ({max_chunk_size}) is larger than recommended "
                    f"({self.RECOMMENDED_MAX_CHUNK_SIZE}). This may cause issues with "
                    "overhead."
                )

    def _validate_live_api(self):
        """Validates configuration against live Discord API (bot token check)."""
        url = "https://discord.com/api/v10/users/@me"
        headers = {
            "Authorization": f"Bot {self.config['bot_token']}"
        }
        
        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers)
                if response.status_code == 200:
                    return True
                elif response.status_code == 401:
                    self.errors.append("Bot token is invalid or unauthorized.")
                    return False
                else:
                    self.errors.append(
                        f"Unexpected response from Discord API when validating bot token: "
                        f"HTTP {response.status_code}"
                    )
                    return False
        except httpx.RequestError as e:
            self.errors.append(f"Failed to validate bot token: {str(e)}")
            return False

    def get_errors(self):
        """Returns list of validation errors."""
        return self.errors.copy()

    def get_warnings(self):
        """Returns list of validation warnings."""
        return self.warnings.copy()
    
    def get_validation_report(self):
        """Returns a formatted validation report."""
        report = []
        
        if not self.errors and not self.warnings:
            report.append("[+] Configuration is valid")
        else:
            if self.errors:
                report.append(f"[x] {len(self.errors)} error(s) found:")
                for error in self.errors:
                    report.append(f"  - {error}")
            
            if self.warnings:
                report.append(f"[!] {len(self.warnings)} warning(s):")
                for warning in self.warnings:
                    report.append(f"  - {warning}")
        
        return "\n".join(report)