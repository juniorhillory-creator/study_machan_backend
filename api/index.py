"""Expose the FastAPI app as a Vercel Python function."""  # Explain why this small file exists.

from main import app  # Give Vercel the FastAPI application defined by the project entry point.

__all__ = ["app"]  # Make the exported application name clear to deployment tools.
