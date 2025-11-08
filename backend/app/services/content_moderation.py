"""Content moderation service for validating user input."""

import re
from typing import NamedTuple

from app.exceptions import InvalidQuestionError


class ModerationResult(NamedTuple):
    """Result of content moderation check."""

    is_valid: bool
    reason: str | None = None


class ContentModerationService:
    """Service for moderating user-generated content.

    Performs validation checks to prevent:
    - Profanity and offensive language
    - Prompt injection attempts
    - Spam and excessive repetition
    - Overly long inputs
    """

    # Maximum allowed question length
    MAX_QUESTION_LENGTH = 500

    # Profanity patterns (basic list - expand as needed)
    PROFANITY_PATTERNS = [
        r"\b(fuck|shit|damn|bitch|asshole|bastard|cunt|dick)\b",
    ]

    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|all|your)\s+instructions?",
        r"ignore\s+all\s+",  # Added to catch "ignore all your"
        r"you\s+are\s+now",
        r"act\s+as\s+a?",
        r"pretend\s+to\s+be",
        r"system\s*:\s*",
        r"forget\s+(everything|all|your)",
        r"disregard\s+(previous|all|your)",
    ]

    # Spam patterns
    SPAM_PATTERNS = [
        r"(.)\1{9,}",  # 10+ repeated characters (adjusted threshold)
        r"(\w+)\s+\1\s+\1",  # Same word repeated 3+ times
    ]

    def __init__(self):
        """Initialize content moderation service with compiled regex patterns."""
        self.profanity_regex = re.compile(
            "|".join(self.PROFANITY_PATTERNS), re.IGNORECASE
        )
        self.injection_regex = re.compile(
            "|".join(self.INJECTION_PATTERNS), re.IGNORECASE
        )
        # Compile spam patterns separately since they use backreferences
        self.spam_regexes = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.SPAM_PATTERNS
        ]

    def validate_question(self, question: str) -> ModerationResult:
        """Validate a question against moderation rules.

        Args:
            question: The user's question to validate

        Returns:
            ModerationResult with validation status and optional reason

        Raises:
            InvalidQuestionError: If question violates moderation rules
        """
        # Check for empty or whitespace-only questions
        if not question or not question.strip():
            return ModerationResult(
                is_valid=False, reason="Question cannot be empty"
            )

        # Check length
        if len(question) > self.MAX_QUESTION_LENGTH:
            return ModerationResult(
                is_valid=False,
                reason=f"Question exceeds maximum length of {self.MAX_QUESTION_LENGTH} characters",
            )

        # Check for profanity
        if self.profanity_regex.search(question):
            return ModerationResult(
                is_valid=False, reason="Question contains inappropriate language"
            )

        # Check for prompt injection attempts
        if self.injection_regex.search(question):
            return ModerationResult(
                is_valid=False,
                reason="Question appears to be attempting prompt manipulation",
            )

        # Check for spam patterns
        for spam_regex in self.spam_regexes:
            if spam_regex.search(question):
                return ModerationResult(
                    is_valid=False, reason="Question contains spam patterns"
                )

        return ModerationResult(is_valid=True)

    def validate_or_raise(self, question: str) -> None:
        """Validate a question and raise exception if invalid.

        Args:
            question: The user's question to validate

        Raises:
            InvalidQuestionError: If question violates moderation rules
        """
        result = self.validate_question(question)
        if not result.is_valid:
            raise InvalidQuestionError(result.reason)
