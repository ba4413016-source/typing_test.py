"""mr.typing entry point. Run with: uvicorn main:app --host 0.0.0.0 --port $PORT."""

from typing_app.api import create_app

app = create_app()

if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")), proxy_headers=True
    )
