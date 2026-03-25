"""
app/utils/errors.py
====================
Custom exception classes. Raising these lets the API layer
return consistent JSON error responses with the right HTTP codes.
"""


class PromptCraftError(Exception):
    """Base class for all application errors."""
    http_status: int = 500
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str = ""):
        self.message = message or self.default_message
        super().__init__(self.message)


class APIKeyMissingError(PromptCraftError):
    http_status = 401
    default_message = "No API key set. Please connect your Anthropic API key."


class APIKeyInvalidError(PromptCraftError):
    http_status = 401
    default_message = "API key rejected by Anthropic. Please check your key."


class AnthropicTimeoutError(PromptCraftError):
    http_status = 504
    default_message = "Request to Anthropic timed out. Please try again."


class AnthropicAPIError(PromptCraftError):
    http_status = 502
    default_message = "Anthropic API returned an error."


class InvalidInputError(PromptCraftError):
    http_status = 400
    default_message = "Invalid input provided."


class HistoryNotFoundError(PromptCraftError):
    http_status = 404
    default_message = "History entry not found."


class JSONParseError(PromptCraftError):
    http_status = 500
    default_message = "Failed to parse AI response as JSON."
