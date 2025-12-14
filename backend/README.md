# Memexia Backend

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install fastapi sqlalchemy uvicorn
    ```

2.  **Run the Server**:
    Navigate to the `backend` directory and run:
    ```bash
    python -m uvicorn src.memexia_backend.main:app --reload
    ```

3.  **API Documentation**:
    Once running, visit `http://127.0.0.1:8000/docs` for the interactive API documentation (Swagger UI).

## Project Structure

-   `models/`: Database models (SQLAlchemy).
-   `schemas/`: Pydantic models for API request/response.
-   `routers/`: API endpoints.
-   `services/`: Business logic (Graph operations, AI integration).
-   `utils/`: Configuration and utilities.
-   `database.py`: Database connection setup.
-   `main.py`: Application entry point.
