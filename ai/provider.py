"""Abstract AI provider interface."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def get_response(self, prompt: str, context: str = "") -> str:
        """Get a text response from the AI provider."""
        ...

    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str, context: str = "") -> str:
        """Analyze an image and return AI response."""
        ...

    @abstractmethod
    def stream_response(self, prompt: str, context: str = "", callback=None) -> str:
        """Stream response line-by-line, calling callback for each line. Returns full response."""
        ...
