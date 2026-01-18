"""Custom exception classes for Aura application."""


class AuraException(Exception):
    """Base exception for Aura application."""
    pass


class CrawlerException(AuraException):
    """Exception raised during web crawling."""
    pass


class SEOAnalysisException(AuraException):
    """Exception raised during SEO analysis."""
    pass


class LLMAnalysisException(AuraException):
    """Exception raised during LLM integration."""
    pass


class AnalysisException(AuraException):
    """Exception raised during general analysis operations."""
    pass


class ValidationException(AuraException):
    """Exception raised for validation errors."""
    pass
