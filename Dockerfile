# Use a stable Python with good wheel support for pyarrow & Streamlit
FROM python:3.11-slim

# Avoid Python buffering and create app directory
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install basic system dependencies (if you later add libs that need compiling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker build caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project into the image
COPY . /app

# Expose Streamlit default port
EXPOSE 8501

# Default command: run the Streamlit app
CMD ["streamlit", "run", "app/front.py", "--server.port=8501", "--server.address=0.0.0.0"]
