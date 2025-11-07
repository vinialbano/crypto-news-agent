"""Custom exception hierarchy for the application."""


class CryptoNewsAgentError(Exception):
    """Base exception for all application errors."""

    pass


# News feature exceptions
class NewsFeatureError(CryptoNewsAgentError):
    """Base exception for news feature errors."""

    pass


class DuplicateArticleError(NewsFeatureError):
    """Raised when attempting to create an article that already exists."""

    pass


class RSSFetchError(NewsFeatureError):
    """Raised when RSS feed fetching fails."""

    pass


class ArticleProcessingError(NewsFeatureError):
    """Raised when article processing fails."""

    pass


# Infrastructure exceptions
class InfrastructureError(CryptoNewsAgentError):
    """Base exception for infrastructure errors."""

    pass


class EmbeddingGenerationError(InfrastructureError):
    """Raised when embedding generation fails."""

    pass


class DatabaseError(InfrastructureError):
    """Raised when database operations fail."""

    pass


# Questions feature exceptions
class QuestionsFeatureError(CryptoNewsAgentError):
    """Base exception for questions feature errors."""

    pass


class RAGError(QuestionsFeatureError):
    """Raised when RAG processing fails."""

    pass


class InsufficientContextError(QuestionsFeatureError):
    """Raised when insufficient context is available to answer a question."""

    pass


class InvalidQuestionError(QuestionsFeatureError):
    """Raised when a question violates content moderation rules."""

    pass
