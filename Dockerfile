FROM python:3.11-slim

WORKDIR /app

# Copy requirements and installation script first for better Docker layer caching
COPY requirements.txt requirements-build.txt install_deps.sh ./

# Create virtual environment and install dependencies
RUN python -m venv --copies /opt/venv && \
    . /opt/venv/bin/activate && \
    ./install_deps.sh

# Set environment path
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Expose port (adjust as needed)
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]