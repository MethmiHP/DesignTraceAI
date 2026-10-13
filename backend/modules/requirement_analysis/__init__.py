# Exposes the Requirement Analysis router so it can be imported
# and registered easily by the main FastAPI application.

from modules.requirement_analysis.controller import router

__all__ = ["router"]