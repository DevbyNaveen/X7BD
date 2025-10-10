"""
OpenTelemetry Distributed Tracing Module

Enterprise-grade distributed tracing for microservices architecture.
Provides observability across all services with trace propagation.
"""

import os
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
import logging

logger = logging.getLogger(__name__)


class TelemetryManager:
    """
    OpenTelemetry telemetry manager for distributed tracing
    
    Features:
    - Automatic instrumentation for FastAPI, HTTPX, Redis, SQLAlchemy
    - OTLP export to Jaeger/Tempo/other backends
    - Context propagation across services
    - Custom span attributes and events
    - Error tracking and status codes
    """
    
    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        environment: str = "production",
        otlp_endpoint: Optional[str] = None
    ):
        """
        Initialize telemetry manager
        
        Args:
            service_name: Name of the service
            service_version: Version of the service
            environment: Deployment environment
            otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4317")
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize OpenTelemetry tracing"""
        if self._initialized:
            return
        
        try:
            # Create resource with service information
            resource = Resource.create({
                SERVICE_NAME: self.service_name,
                SERVICE_VERSION: self.service_version,
                DEPLOYMENT_ENVIRONMENT: self.environment
            })
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            
            # Create OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_endpoint,
                insecure=True  # Use TLS in production
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            self.tracer_provider.add_span_processor(span_processor)
            
            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)
            
            # Get tracer
            self.tracer = trace.get_tracer(self.service_name, self.service_version)
            
            # Instrument libraries
            self._instrument_libraries()
            
            self._initialized = True
            logger.info(f"OpenTelemetry initialized for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}", exc_info=True)
            raise
    
    def _instrument_libraries(self):
        """Automatically instrument common libraries"""
        try:
            # Instrument HTTPX for HTTP client tracing
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumentation enabled")
            
            # Instrument Redis
            RedisInstrumentor().instrument()
            logger.info("Redis instrumentation enabled")
            
        except Exception as e:
            logger.warning(f"Some instrumentations failed: {e}")
    
    def instrument_fastapi(self, app):
        """
        Instrument FastAPI application
        
        Args:
            app: FastAPI application instance
        """
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}", exc_info=True)
    
    def instrument_sqlalchemy(self, engine):
        """
        Instrument SQLAlchemy engine
        
        Args:
            engine: SQLAlchemy engine instance
        """
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument SQLAlchemy: {e}", exc_info=True)
    
    def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL
    ):
        """
        Create a new span
        
        Args:
            name: Span name
            attributes: Span attributes
            kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
        
        Returns:
            Span context manager
        """
        if not self._initialized:
            self.initialize()
        
        span = self.tracer.start_span(name, kind=kind)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        return span
    
    def add_span_event(self, span: trace.Span, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add event to current span
        
        Args:
            span: Span to add event to
            name: Event name
            attributes: Event attributes
        """
        span.add_event(name, attributes=attributes or {})
    
    def set_span_error(self, span: trace.Span, error: Exception):
        """
        Mark span as error
        
        Args:
            span: Span to mark as error
            error: Exception that occurred
        """
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)
    
    def get_current_span(self) -> Optional[trace.Span]:
        """Get current active span"""
        return trace.get_current_span()
    
    def inject_context(self, carrier: Dict[str, str]):
        """
        Inject trace context into carrier (for propagation)
        
        Args:
            carrier: Dictionary to inject context into (e.g., HTTP headers)
        """
        propagator = TraceContextTextMapPropagator()
        propagator.inject(carrier)
    
    def extract_context(self, carrier: Dict[str, str]):
        """
        Extract trace context from carrier
        
        Args:
            carrier: Dictionary containing context (e.g., HTTP headers)
        
        Returns:
            Extracted context
        """
        propagator = TraceContextTextMapPropagator()
        return propagator.extract(carrier)
    
    def shutdown(self):
        """Shutdown telemetry and flush spans"""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("OpenTelemetry shutdown complete")


# Decorator for tracing functions
def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace function execution
    
    Args:
        name: Custom span name (defaults to function name)
        attributes: Additional span attributes
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            span_name = name or f"{func.__module__}.{func.__name__}"
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        def sync_wrapper(*args, **kwargs):
            span_name = name or f"{func.__module__}.{func.__name__}"
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Context manager for manual span creation
class TracedOperation:
    """Context manager for creating traced operations"""
    
    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.name = name
        self.attributes = attributes or {}
        self.span = None
        self.tracer = trace.get_tracer(__name__)
    
    def __enter__(self):
        self.span = self.tracer.start_span(self.name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
        else:
            self.span.set_status(Status(StatusCode.OK))
        self.span.end()
