# Embroidery Stitch Estimator Service

A FastAPI-based service that estimates the number of embroidery stitches required for a design based on an image and physical dimensions.

## Features

- **Stitch Estimation**: Calculates total stitch count based on filled area and edge length.
- **Detailed Breakdown**: Returns filled area (sq inches), edge length (inches), and stitch counts for both.
- **Image Processing**: Automatically removes backgrounds and processes images for accurate estimation.
- **API**: Simple REST API endpoint for easy integration.

## Requirements

- Python 3.8+
- OpenCV (headless version used)
- NumPy
- FastAPI
- Uvicorn

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd embroidery-stitch-calculator
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Start the server:**

    ```bash
    uvicorn app.main:app --reload
    ```

    The server will start at `http://127.0.0.1:8000`.

2.  **API Documentation:**

    Once the server is running, you can access the interactive API documentation at:

    - Swagger UI: `http://127.0.0.1:8000/docs`
    - ReDoc: `http://127.0.0.1:8000/redoc`

3.  **Estimate Stitches:**

    Send a POST request to `/estimate` with the image URL and desired width in inches.

    **Example Request (cURL):**

    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/estimate' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "image_url": "https://example.com/logo.png",
      "width_inches": 5.0
    }'
    ```

    **Example Response:**

    ```json
    {
      "stitch_count": 12500,
      "details": {
        "filled_area_sq_inches": 6.5,
        "edge_length_inches": 25.0,
        "fill_stitches": 10400,
        "edge_stitches": 2100,
        "physical_dimensions": "5.00x3.50 inches"
      }
    }
    ```

## Project Structure

- `app/main.py`: FastAPI application entry point and API endpoints.
- `app/estimator.py`: Core logic for image processing and stitch calculation.
- `app/models.py`: Pydantic models for request and response validation.
- `app/utils.py`: Utility functions for image downloading and processing.
- `requirements.txt`: Project dependencies.
