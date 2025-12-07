from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from .models import EstimationRequest, EstimationResponse
from .utils import download_image
from .estimator import StitchEstimator
from .logger import RequestLogger
import uvicorn

app = FastAPI(title="Embroidery Stitch Estimator")
logger = RequestLogger()

@app.get("/", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
async def web_interface():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Embroidery Stitch Estimator</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 600px;
                width: 100%;
                padding: 40px;
            }
            
            h1 {
                color: #333;
                font-size: 28px;
                margin-bottom: 8px;
                text-align: center;
            }
            
            .subtitle {
                color: #666;
                text-align: center;
                margin-bottom: 32px;
                font-size: 14px;
            }
            
            .form-group {
                margin-bottom: 24px;
            }
            
            .input-method-toggle {
                display: flex;
                gap: 12px;
                margin-bottom: 16px;
                background: #f0f0f0;
                padding: 4px;
                border-radius: 8px;
            }
            
            .method-btn {
                flex: 1;
                padding: 10px;
                background: transparent;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                color: #666;
            }
            
            .method-btn.active {
                background: white;
                color: #667eea;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .input-section {
                display: none;
            }
            
            .input-section.active {
                display: block;
            }
            
            .upload-area {
                border: 3px dashed #d0d0d0;
                border-radius: 12px;
                padding: 40px 20px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: #fafafa;
            }
            
            .upload-area:hover {
                border-color: #667eea;
                background: #f5f7ff;
            }
            
            .upload-area.dragover {
                border-color: #667eea;
                background: #e8ebff;
                transform: scale(1.02);
            }
            
            .upload-icon {
                font-size: 48px;
                margin-bottom: 12px;
                color: #667eea;
            }
            
            .upload-text {
                color: #333;
                font-weight: 600;
                margin-bottom: 8px;
            }
            
            .upload-hint {
                color: #666;
                font-size: 13px;
            }
            
            .file-input {
                display: none;
            }
            
            .uploaded-preview {
                display: none;
                margin-top: 16px;
                padding: 12px;
                background: #f0f7ff;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            
            .uploaded-preview.active {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .preview-icon {
                font-size: 24px;
            }
            
            .preview-info {
                flex: 1;
            }
            
            .preview-name {
                font-weight: 600;
                color: #333;
                margin-bottom: 4px;
            }
            
            .preview-url {
                font-size: 12px;
                color: #667eea;
                word-break: break-all;
            }
            
            .remove-file {
                background: #f44;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
            }
            
            .remove-file:hover {
                background: #d33;
            }
            
            label {
                display: block;
                color: #333;
                font-weight: 600;
                margin-bottom: 8px;
                font-size: 14px;
            }
            
            .input-with-description {
                display: flex;
                gap: 12px;
                align-items: center;
            }
            
            .input-with-description input {
                flex: 0 0 150px;
            }
            
            .input-description {
                flex: 1;
                font-size: 12px;
                color: #666;
                line-height: 1.4;
            }
            
            input {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                transition: all 0.3s ease;
            }
            
            input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .more-toggle {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                color: #667eea;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                padding: 12px;
                margin-bottom: 16px;
                border-radius: 8px;
                transition: background 0.2s ease;
                user-select: none;
            }
            
            .more-toggle:hover {
                background: #f5f5f5;
            }
            
            .arrow {
                transition: transform 0.3s ease;
                font-size: 18px;
            }
            
            .arrow.open {
                transform: rotate(180deg);
            }
            
            .advanced-params {
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.4s ease;
            }
            
            .advanced-params.open {
                max-height: 2000px;
            }
            
            .advanced-content {
                padding: 20px;
                background: #f8f9fa;
                border-radius: 12px;
                margin-bottom: 20px;
            }
            
            .section-title {
                font-size: 16px;
                font-weight: 700;
                color: #333;
                margin-bottom: 16px;
                padding-bottom: 8px;
                border-bottom: 2px solid #667eea;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .reset-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .reset-btn:hover {
                background: #5568d3;
                transform: translateY(-1px);
            }
            
            .reset-btn:active {
                transform: translateY(0);
            }
            
            .param-group {
                margin-bottom: 16px;
            }
            
            .param-group:last-child {
                margin-bottom: 0;
            }
            
            .btn {
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            
            .btn:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            }
            
            .btn:active:not(:disabled) {
                transform: translateY(0);
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .loading {
                display: none;
                text-align: center;
                margin-top: 20px;
                color: #667eea;
                font-weight: 600;
            }
            
            .loading.active {
                display: block;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .result {
                display: none;
                margin-top: 32px;
                padding: 24px;
                background: #f8f9fa;
                border-radius: 12px;
                border-left: 4px solid #667eea;
            }
            
            .result.active {
                display: block;
                animation: slideIn 0.4s ease;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .result h2 {
                color: #333;
                font-size: 20px;
                margin-bottom: 16px;
            }
            
            .stitch-count {
                font-size: 36px;
                font-weight: 700;
                color: #667eea;
                margin-bottom: 20px;
            }
            
            .details-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin-top: 16px;
            }
            
            .detail-item {
                background: white;
                padding: 12px;
                border-radius: 8px;
            }
            
            .detail-label {
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .detail-value {
                font-size: 18px;
                font-weight: 600;
                color: #333;
                margin-top: 4px;
            }
            
            .error {
                display: none;
                margin-top: 20px;
                padding: 16px;
                background: #fee;
                border-left: 4px solid #f44;
                border-radius: 8px;
                color: #c33;
            }
            
            .error.active {
                display: block;
                animation: slideIn 0.4s ease;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧵 Embroidery Stitch Estimator</h1>
            <p class="subtitle">Calculate stitch count for your embroidery designs</p>
            
            <form id="estimateForm">
                <div class="form-group">
                    <label>Image Source</label>
                    <div class="input-method-toggle">
                        <button type="button" class="method-btn active" data-method="upload">Upload Image</button>
                        <button type="button" class="method-btn" data-method="url">Image URL</button>
                    </div>
                    
                    <div class="input-section active" id="uploadSection">
                        <div class="upload-area" id="uploadArea">
                            <div class="upload-icon">📤</div>
                            <div class="upload-text">Drag & Drop your image here</div>
                            <div class="upload-hint">or click to browse (PNG, JPG, JPEG)</div>
                        </div>
                        <input type="file" id="fileInput" class="file-input" accept="image/png,image/jpeg,image/jpg">
                        
                        <div class="uploaded-preview" id="uploadedPreview">
                            <div class="preview-icon">✅</div>
                            <div class="preview-info">
                                <div class="preview-name" id="previewName"></div>
                                <div class="preview-url" id="previewUrl"></div>
                            </div>
                            <button type="button" class="remove-file" id="removeFile">Remove</button>
                        </div>
                    </div>
                    
                    <div class="input-section" id="urlSection">
                        <input 
                            type="url" 
                            id="imageUrl" 
                            name="image_url" 
                            placeholder="https://example.com/image.png"
                        >
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="widthInches">Width (inches)</label>
                    <input 
                        type="number" 
                        id="widthInches" 
                        name="width_inches" 
                        placeholder="4.0"
                        step="0.01"
                        min="0.1"
                        required
                    >
                </div>
                
                <div class="more-toggle" id="moreToggle">
                    <span class="arrow" id="arrow">▼</span>
                    <span>More</span>
                </div>
                
                <div class="advanced-params" id="advancedParams">
                    <div class="advanced-content">
                        <div class="section-title">
                            <span>Density Constants</span>
                            <button type="button" class="reset-btn" id="resetBtn">Reset to Default</button>
                        </div>
                        
                        <div class="param-group">
                            <label for="fillDensity">Fill Density (stitches/sq inch)</label>
                            <div class="input-with-description">
                                <input type="number" id="fillDensity" value="2200" step="100" min="1000">
                                <span class="input-description">Tatami fill density. Lower values reduce stitch count</span>
                            </div>
                        </div>
                        
                        <div class="param-group">
                            <label for="satinSpacing">Satin Spacing (inches)</label>
                            <div class="input-with-description">
                                <input type="number" id="satinSpacing" value="0.0138" step="0.0001" min="0.001">
                                <span class="input-description">Space between satin stitches (0.35mm default)</span>
                            </div>
                        </div>
                        
                        <div class="param-group">
                            <label for="runningDensity">Running Stitch Density (stitches/inch)</label>
                            <div class="input-with-description">
                                <input type="number" id="runningDensity" value="35" step="1" min="10">
                                <span class="input-description">Stitches per inch for running/outline stitches</span>
                            </div>
                        </div>
                        
                        <div class="section-title" style="margin-top: 24px;">Global Factors</div>
                        
                        <div class="param-group">
                            <label for="stitchesPerColor">Stitches Per Color Change</label>
                            <div class="input-with-description">
                                <input type="number" id="stitchesPerColor" value="20" step="1" min="0">
                                <span class="input-description">Additional stitches for trim, tie-off, and tie-in</span>
                            </div>
                        </div>
                        
                        <div class="param-group">
                            <label for="underlayFillRatio">Underlay Fill Ratio</label>
                            <div class="input-with-description">
                                <input type="number" id="underlayFillRatio" value="0.35" step="0.05" min="0" max="1">
                                <span class="input-description">Lattice underlay ratio for fill areas (35% default)</span>
                            </div>
                        </div>
                        
                        <div class="section-title" style="margin-top: 24px;">Width Thresholds</div>
                        
                        <div class="param-group">
                            <label for="satinMinWidth">Satin Minimum Width (inches)</label>
                            <div class="input-with-description">
                                <input type="number" id="satinMinWidth" value="0.02" step="0.001" min="0.001">
                                <span class="input-description">Minimum width for satin classification (~0.5mm)</span>
                            </div>
                        </div>
                        
                        <div class="param-group">
                            <label for="satinMaxWidth">Satin Maximum Width (inches)</label>
                            <div class="input-with-description">
                                <input type="number" id="satinMaxWidth" value="0.35" step="any" min="0.001">
                                <span class="input-description">Maximum width for satin classification (~9mm)</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="btn" id="submitBtn">
                    Execute Estimation
                </button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Processing your design...</p>
            </div>
            
            <div class="error" id="error"></div>
            
            <div class="result" id="result">
                <h2>Estimation Results</h2>
                <div class="stitch-count" id="stitchCount"></div>
                
                <div class="details-grid">
                    <div class="detail-item">
                        <div class="detail-label">Fill Stitches</div>
                        <div class="detail-value" id="fillStitches">-</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Satin Stitches</div>
                        <div class="detail-value" id="satinStitches">-</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Running Stitches</div>
                        <div class="detail-value" id="runningStitches">-</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Color Changes</div>
                        <div class="detail-value" id="colorChanges">-</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Underlay Stitches</div>
                        <div class="detail-value" id="underlayStitches">-</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Color Count</div>
                        <div class="detail-value" id="colorCount">-</div>
                    </div>
                </div>
                
                <div class="detail-item" style="margin-top: 12px;">
                    <div class="detail-label">Physical Dimensions</div>
                    <div class="detail-value" id="dimensions">-</div>
                </div>
            </div>
        </div>
        
        <script>
            const form = document.getElementById('estimateForm');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const error = document.getElementById('error');
            const submitBtn = document.getElementById('submitBtn');
            const moreToggle = document.getElementById('moreToggle');
            const advancedParams = document.getElementById('advancedParams');
            const arrow = document.getElementById('arrow');
            const resetBtn = document.getElementById('resetBtn');
            
            // Image source elements
            const methodBtns = document.querySelectorAll('.method-btn');
            const uploadSection = document.getElementById('uploadSection');
            const urlSection = document.getElementById('urlSection');
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const uploadedPreview = document.getElementById('uploadedPreview');
            const previewName = document.getElementById('previewName');
            const previewUrl = document.getElementById('previewUrl');
            const removeFile = document.getElementById('removeFile');
            const imageUrlInput = document.getElementById('imageUrl');
            
            let uploadedImageUrl = null;
            let currentMethod = 'upload';
            
            // Default values
            const defaults = {
                fillDensity: 2200,
                satinSpacing: 0.0138,
                runningDensity: 35,
                stitchesPerColor: 20,
                underlayFillRatio: 0.35,
                satinMinWidth: 0.02,
                satinMaxWidth: 0.35
            };
            
            // Toggle between upload and URL
            methodBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    methodBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    const method = btn.dataset.method;
                    currentMethod = method;
                    
                    if (method === 'upload') {
                        uploadSection.classList.add('active');
                        urlSection.classList.remove('active');
                    } else {
                        uploadSection.classList.remove('active');
                        urlSection.classList.add('active');
                    }
                });
            });
            
            // Upload area click
            uploadArea.addEventListener('click', () => {
                fileInput.click();
            });
            
            // Drag and drop handlers
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFileUpload(files[0]);
                }
            });
            
            // File input change
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFileUpload(e.target.files[0]);
                }
            });
            
            // Remove file
            removeFile.addEventListener('click', () => {
                uploadedImageUrl = null;
                uploadedPreview.classList.remove('active');
                fileInput.value = '';
            });
            
            // Handle file upload
            async function handleFileUpload(file) {
                // Validate file type
                const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
                if (!validTypes.includes(file.type)) {
                    error.textContent = 'Please upload a valid image file (PNG, JPG, JPEG)';
                    error.classList.add('active');
                    return;
                }
                
                error.classList.remove('active');
                loading.classList.add('active');
                
                try {
                    // Get file extension
                    const fileExtension = file.name.split('.').pop().toLowerCase();
                    
                    // Create form data
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('fileExtension', fileExtension);
                    
                    // Upload to cloud
                    const response = await fetch('https://cloud.printmood.com', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('Upload failed');
                    }
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        throw new Error(data.message || 'Upload failed');
                    }
                    
                    // Store the uploaded URL
                    uploadedImageUrl = data.data.url;
                    
                    // Show preview
                    previewName.textContent = data.data.fileName;
                    previewUrl.textContent = data.data.url;
                    uploadedPreview.classList.add('active');
                    
                } catch (err) {
                    error.textContent = 'Upload failed: ' + err.message;
                    error.classList.add('active');
                } finally {
                    loading.classList.remove('active');
                }
            }
            
            // Reset to default values
            resetBtn.addEventListener('click', () => {
                document.getElementById('fillDensity').value = defaults.fillDensity;
                document.getElementById('satinSpacing').value = defaults.satinSpacing;
                document.getElementById('runningDensity').value = defaults.runningDensity;
                document.getElementById('stitchesPerColor').value = defaults.stitchesPerColor;
                document.getElementById('underlayFillRatio').value = defaults.underlayFillRatio;
                document.getElementById('satinMinWidth').value = defaults.satinMinWidth;
                document.getElementById('satinMaxWidth').value = defaults.satinMaxWidth;
            });
            
            // Toggle advanced parameters
            moreToggle.addEventListener('click', () => {
                advancedParams.classList.toggle('open');
                arrow.classList.toggle('open');
            });
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                // Get image URL based on current method
                let imageUrl;
                if (currentMethod === 'upload') {
                    if (!uploadedImageUrl) {
                        error.textContent = 'Please upload an image first';
                        error.classList.add('active');
                        return;
                    }
                    imageUrl = uploadedImageUrl;
                } else {
                    imageUrl = imageUrlInput.value;
                    if (!imageUrl) {
                        error.textContent = 'Please enter an image URL';
                        error.classList.add('active');
                        return;
                    }
                }
                
                // Hide previous results
                result.classList.remove('active');
                error.classList.remove('active');
                
                // Show loading
                loading.classList.add('active');
                submitBtn.disabled = true;
                
                const formData = {
                    image_url: imageUrl,
                    width_inches: parseFloat(document.getElementById('widthInches').value),
                    parameters: {
                        fill_density: parseFloat(document.getElementById('fillDensity').value),
                        satin_spacing_inch: parseFloat(document.getElementById('satinSpacing').value),
                        running_density_per_inch: parseFloat(document.getElementById('runningDensity').value),
                        stitches_per_color: parseInt(document.getElementById('stitchesPerColor').value),
                        underlay_fill_ratio: parseFloat(document.getElementById('underlayFillRatio').value),
                        satin_min_width_inch: parseFloat(document.getElementById('satinMinWidth').value),
                        satin_max_width_inch: parseFloat(document.getElementById('satinMaxWidth').value)
                    }
                };
                
                try {
                    const response = await fetch('/estimate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(formData)
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Estimation failed');
                    }
                    
                    const data = await response.json();
                    
                    // Display results
                    document.getElementById('stitchCount').textContent = 
                        data.stitch_count.toLocaleString() + ' stitches';
                    document.getElementById('fillStitches').textContent = 
                        data.details.fill_stitches.toLocaleString();
                    document.getElementById('satinStitches').textContent = 
                        data.details.satin_stitches.toLocaleString();
                    document.getElementById('runningStitches').textContent = 
                        data.details.running_stitches.toLocaleString();
                    document.getElementById('colorChanges').textContent = 
                        data.details.color_change_stitches.toLocaleString();
                    document.getElementById('underlayStitches').textContent = 
                        Math.round(data.details.underlay_stitches).toLocaleString();
                    document.getElementById('colorCount').textContent = 
                        data.details.color_count;
                    document.getElementById('dimensions').textContent = 
                        data.details.physical_dimensions;
                    
                    result.classList.add('active');
                    
                } catch (err) {
                    error.textContent = err.message;
                    error.classList.add('active');
                } finally {
                    loading.classList.remove('active');
                    submitBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/estimate", response_model=EstimationResponse)
async def estimate_stitches(request: EstimationRequest):
    try:
        # Download image
        image_bytes = await download_image(str(request.image_url))
        
        # Initialize estimator with parameters
        estimator = StitchEstimator(
            image_bytes, 
            request.width_inches,
            parameters=request.parameters
        )
        
        # Get estimation
        result = estimator.estimate()
        
        # Log the request
        print(f"Logging request for: {request.image_url}")
        logger.log_request(
            image_url=str(request.image_url),
            width_inches=request.width_inches,
            result=result
        )
        print("Request logged successfully")
        
        return EstimationResponse(
            stitch_count=result["stitch_count"],
            details=result["details"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(limit: int = None):
    """Get estimation logs. Optional limit parameter for most recent N entries."""
    logs = logger.get_logs(limit=limit)
    return JSONResponse(content={"total": len(logs), "logs": logs})

@app.delete("/logs")
async def clear_logs():
    """Clear all estimation logs."""
    logger.clear_logs()
    return JSONResponse(content={"message": "Logs cleared successfully"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)