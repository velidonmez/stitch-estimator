# Embroidery Stitch Estimator Service

A FastAPI-based service that estimates the number of embroidery stitches required for a design based on an image and physical dimensions.

## Features

- **Web Interface**: Beautiful, user-friendly web interface at `/` or `/app`
- **Image Upload**: Drag & drop or browse to upload images directly
- **Image URL Support**: Alternative option to provide image URLs
- **Customizable Parameters**: Advanced settings for fine-tuning estimation algorithms
- **Stitch Estimation**: Calculates total stitch count based on filled area, edge length, and stitch types
- **Detailed Breakdown**: Returns filled area, edge length, and stitch counts for fill, satin, and running stitches
- **Image Processing**: Automatically removes backgrounds and processes images for accurate estimation
- **Request Logging**: Automatically logs all estimation requests for analysis
- **REST API**: Simple API endpoints for programmatic access

## Requirements

- Python 3.8+
- OpenCV (headless version)
- NumPy
- FastAPI
- Uvicorn
- httpx
- Pydantic

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

### Start the Server

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### Web Interface

Once the server is running, open your browser and navigate to:

- **Main Interface**: `http://127.0.0.1:8000/app`

#### Using the Web Interface:

1. **Choose Input Method**:
   - **Upload Image** (default): Drag & drop or click to browse for an image file
   - **Image URL**: Paste a direct URL to an image

2. **Set Width**: Enter the desired width in inches

3. **Advanced Parameters** (optional): Click "More" to customize:
   - Fill Density
   - Satin Spacing
   - Running Stitch Density
   - Stitches Per Color Change
   - Underlay Fill Ratio
   - Satin Width Thresholds
   
4. **Execute Estimation**: Click the button to get results

5. **View Results**: See detailed stitch count breakdown

### API Documentation

Interactive API documentation available at:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### API Endpoints

#### Estimate Stitches

**POST** `/estimate`

Calculate stitch count for an embroidery design.

**Request Body:**

```json
{
  "image_url": "https://example.com/logo.png",
  "width_inches": 5.0,
  "parameters": {
    "fill_density": 2200.0,
    "satin_spacing_inch": 0.0138,
    "running_density_per_inch": 35.0,
    "stitches_per_color": 20,
    "underlay_fill_ratio": 0.35,
    "satin_min_width_inch": 0.02,
    "satin_max_width_inch": 0.35
  }
}
```

**Note**: The `parameters` field is optional. If not provided, default values will be used.

**Example Response:**

```json
{
  "stitch_count": 32089,
  "details": {
    "fill_stitches": 22954,
    "satin_stitches": 266,
    "running_stitches": 549,
    "color_change_stitches": 220,
    "underlay_stitches": 8098.59375,
    "color_count": 12,
    "physical_dimensions": "4.00x2.67 inches"
  }
}
```

#### Get Estimation Logs

**GET** `/logs`

Retrieve all logged estimation requests.

**Query Parameters:**
- `limit` (optional): Limit results to the most recent N entries

**Example:**

```bash
# Get all logs
curl http://127.0.0.1:8000/logs

# Get last 10 logs
curl http://127.0.0.1:8000/logs?limit=10
```

**Response:**

```json
{
  "total": 25,
  "logs": [
    {
      "timestamp": "2025-12-06T14:30:45.123456",
      "url": "https://storage.printmood.com/example.png",
      "width": 4.0,
      "stitch_count": 32089,
      "details": {
        "fill_stitches": 22954,
        "satin_stitches": 266,
        "running_stitches": 549,
        "color_change_stitches": 220,
        "underlay_stitches": 8098.59375,
        "color_count": 12,
        "physical_dimensions": "4.00x2.67 inches"
      }
    }
  ]
}
```

#### Clear Logs

**DELETE** `/logs`

Clear all logged estimation requests.

**Example:**

```bash
curl -X DELETE http://127.0.0.1:8000/logs
```

**Response:**

```json
{
  "message": "Logs cleared successfully"
}
```

### cURL Examples

**Basic Estimation:**

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

**Estimation with Custom Parameters:**

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/estimate' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "image_url": "https://example.com/logo.png",
  "width_inches": 5.0,
  "parameters": {
    "fill_density": 2400.0,
    "satin_spacing_inch": 0.015,
    "running_density_per_inch": 40.0
  }
}'
```

## Project Structure

```
embroidery-stitch-calculator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and web interface
│   ├── estimator.py         # Core estimation logic
│   ├── models.py            # Pydantic models
│   ├── utils.py             # Utility functions
│   └── logger.py            # Request logging system
├── requirements.txt         # Project dependencies
├── .gitignore              # Git ignore rules
├── README.md               # This file
└── estimation_logs.json    # Auto-generated log file
```

## Estimation Parameters

### Density Constants

- **Fill Density** (default: 2200 stitches/sq inch): Tatami fill stitch density
- **Satin Spacing** (default: 0.0138 inches): Space between satin stitches (~0.35mm)
- **Running Density** (default: 35 stitches/inch): Running/outline stitch density

### Global Factors

- **Stitches Per Color** (default: 20): Additional stitches for color changes (trim, tie-off, tie-in)
- **Underlay Fill Ratio** (default: 0.35): Lattice underlay as percentage of fill density

### Width Thresholds

- **Satin Min Width** (default: 0.02 inches): Minimum width for satin classification (~0.5mm)
- **Satin Max Width** (default: 0.35 inches): Maximum width for satin classification (~9mm)

## Image Upload

The service supports direct image uploads through the web interface. Images are automatically uploaded to `https://cloud.printmood.com` and then processed for stitch estimation.

**Supported Formats:**
- PNG
- JPG/JPEG

**Upload Methods:**
- Drag & drop
- Click to browse

## Request Logging

All estimation requests are automatically logged to `estimation_logs.json` with the following information:

- Timestamp (ISO format)
- Image URL
- Width (inches)
- Stitch count
- Full estimation details

Logs can be retrieved via the `/logs` endpoint or by directly accessing the JSON file.

## Testing

Run the comparison script to test against reference implementations:

```bash
python compare_with_endpoint.py
```

## Development

To run the server in development mode with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

---

# stitch-estimator

For more information or support, please contact the development team.