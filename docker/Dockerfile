FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY ./services/analytics-dashboard-service/requirements.txt /app/requirements.txt
COPY ./shared/libs/requirements.txt /app/shared_requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r shared_requirements.txt

# Copy shared libraries
COPY ./shared/libs /app/shared/libs

# Copy application code
COPY ./services/analytics-dashboard-service/app /app/app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8050

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8050"]
