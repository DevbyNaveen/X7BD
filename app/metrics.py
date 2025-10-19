"""
Prometheus Metrics Module
Handles metrics registration and prevents duplication errors
"""

from prometheus_client import Counter, REGISTRY
import logging

logger = logging.getLogger(__name__)

def get_or_create_counter(name: str, description: str, labelnames: list = None):
    """Get existing counter or create new one to avoid duplication errors"""
    try:
        # Try to get existing counter
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        else:
            # Create new counter
            return Counter(name, description, labelnames or [])
    except Exception as e:
        logger.warning(f"Metrics registration issue: {e}")
        # Return a dummy counter if there are issues
        return Counter(f"{name}_backup", description, labelnames or [])

# Define metrics
REQUEST_COUNT = get_or_create_counter(
    'x7bd_food_qr_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

PDF_UPLOADS = get_or_create_counter(
    'x7bd_food_qr_pdf_uploads_total',
    'Total PDF uploads',
    ['status']
)
