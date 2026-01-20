"""Entry point for running the application as a module."""

import uvicorn

from app.config import settings


def main() -> None:
    """Run the application server."""
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
