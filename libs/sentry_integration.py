"""
Sentry Error Tracking Integration

Enterprise-grade error tracking and performance monitoring with Sentry.
"""

import os
from typing import Optional, Dict, Any
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

logger = logging.getLogger(__name__)


class SentryManager:
    """
    Sentry error tracking and performance monitoring manager
    
    Features:
    - Automatic error capture and reporting
    - Performance monitoring and tracing
    - Release tracking and deployment notifications
    - User context and custom tags
    - Integration with FastAPI, Redis, HTTPX, SQLAlchemy
    """
    
    def __init__(
        self,
        dsn: Optional[str] = None,
        environment: str = "production",
        service_name: str = "x7ai-service",
        release: Optional[str] = None,
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1
    ):
        """
        Initialize Sentry manager
        
        Args:
            dsn: Sentry DSN (Data Source Name)
            environment: Deployment environment
            service_name: Service name for identification
            release: Release version
            traces_sample_rate: Percentage of transactions to trace (0.0 to 1.0)
            profiles_sample_rate: Percentage of transactions to profile (0.0 to 1.0)
        """
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self.environment = environment
        self.service_name = service_name
        self.release = release or os.getenv("RELEASE_VERSION", "1.0.0")
        self.traces_sample_rate = traces_sample_rate
        self.profiles_sample_rate = profiles_sample_rate
        self._initialized = False
    
    def initialize(self):
        """Initialize Sentry SDK"""
        if self._initialized:
            return
        
        if not self.dsn:
            logger.warning("Sentry DSN not configured. Error tracking disabled.")
            return
        
        try:
            # Configure integrations
            integrations = [
                FastApiIntegration(transaction_style="endpoint"),
                RedisIntegration(),
                HttpxIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
            ]
            
            # Initialize Sentry
            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                release=self.release,
                integrations=integrations,
                traces_sample_rate=self.traces_sample_rate,
                profiles_sample_rate=self.profiles_sample_rate,
                send_default_pii=False,  # Don't send PII by default
                attach_stacktrace=True,
                max_breadcrumbs=50,
                before_send=self._before_send,
                before_breadcrumb=self._before_breadcrumb
            )
            
            # Set service tag
            sentry_sdk.set_tag("service", self.service_name)
            
            self._initialized = True
            logger.info(f"Sentry initialized for {self.service_name} in {self.environment}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)
    
    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Filter/modify events before sending to Sentry
        
        Args:
            event: Sentry event
            hint: Additional context
        
        Returns:
            Modified event or None to drop
        """
        # Filter out specific errors if needed
        if 'exc_info' in hint:
            exc_type, exc_value, tb = hint['exc_info']
            
            # Don't send certain exceptions
            if exc_type.__name__ in ['KeyboardInterrupt', 'SystemExit']:
                return None
        
        return event
    
    def _before_breadcrumb(self, crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Filter/modify breadcrumbs before adding
        
        Args:
            crumb: Breadcrumb data
            hint: Additional context
        
        Returns:
            Modified breadcrumb or None to drop
        """
        # Filter sensitive data from breadcrumbs
        if crumb.get('category') == 'httplib':
            # Remove sensitive headers
            if 'data' in crumb and 'headers' in crumb['data']:
                sensitive_headers = ['authorization', 'cookie', 'x-api-key']
                for header in sensitive_headers:
                    crumb['data']['headers'].pop(header, None)
        
        return crumb
    
    def capture_exception(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        level: str = "error"
    ):
        """
        Capture exception and send to Sentry
        
        Args:
            error: Exception to capture
            context: Additional context
            tags: Custom tags
            level: Error level (debug, info, warning, error, fatal)
        """
        if not self._initialized:
            return
        
        with sentry_sdk.push_scope() as scope:
            # Set level
            scope.level = level
            
            # Add context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            # Add tags
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            
            # Capture exception
            sentry_sdk.capture_exception(error)
    
    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Capture message and send to Sentry
        
        Args:
            message: Message to capture
            level: Message level
            context: Additional context
            tags: Custom tags
        """
        if not self._initialized:
            return
        
        with sentry_sdk.push_scope() as scope:
            # Set level
            scope.level = level
            
            # Add context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            # Add tags
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            
            # Capture message
            sentry_sdk.capture_message(message, level=level)
    
    def set_user(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Set user context for error tracking
        
        Args:
            user_id: User identifier
            email: User email
            username: Username
            additional_data: Additional user data
        """
        if not self._initialized:
            return
        
        user_data = {}
        if user_id:
            user_data["id"] = user_id
        if email:
            user_data["email"] = email
        if username:
            user_data["username"] = username
        if additional_data:
            user_data.update(additional_data)
        
        sentry_sdk.set_user(user_data)
    
    def set_context(self, key: str, value: Dict[str, Any]):
        """
        Set custom context
        
        Args:
            key: Context key
            value: Context data
        """
        if not self._initialized:
            return
        
        sentry_sdk.set_context(key, value)
    
    def set_tag(self, key: str, value: str):
        """
        Set custom tag
        
        Args:
            key: Tag key
            value: Tag value
        """
        if not self._initialized:
            return
        
        sentry_sdk.set_tag(key, value)
    
    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: str = "info",
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Add breadcrumb for debugging context
        
        Args:
            message: Breadcrumb message
            category: Breadcrumb category
            level: Breadcrumb level
            data: Additional data
        """
        if not self._initialized:
            return
        
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    
    def start_transaction(
        self,
        name: str,
        op: str = "http.server",
        description: Optional[str] = None
    ):
        """
        Start performance transaction
        
        Args:
            name: Transaction name
            op: Operation type
            description: Transaction description
        
        Returns:
            Transaction context manager
        """
        if not self._initialized:
            return None
        
        return sentry_sdk.start_transaction(
            name=name,
            op=op,
            description=description
        )
    
    def flush(self, timeout: int = 2):
        """
        Flush pending events to Sentry
        
        Args:
            timeout: Timeout in seconds
        """
        if self._initialized:
            sentry_sdk.flush(timeout=timeout)


# Decorator for capturing function errors
def capture_errors(
    tags: Optional[Dict[str, str]] = None,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
):
    """
    Decorator to automatically capture function errors
    
    Args:
        tags: Custom tags
        context: Additional context
        level: Error level
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                with sentry_sdk.push_scope() as scope:
                    scope.level = level
                    
                    if tags:
                        for key, value in tags.items():
                            scope.set_tag(key, value)
                    
                    if context:
                        for key, value in context.items():
                            scope.set_context(key, value)
                    
                    # Add function context
                    scope.set_context("function", {
                        "name": func.__name__,
                        "module": func.__module__,
                        "args": str(args)[:200],  # Limit size
                        "kwargs": str(kwargs)[:200]
                    })
                    
                    sentry_sdk.capture_exception(e)
                raise
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                with sentry_sdk.push_scope() as scope:
                    scope.level = level
                    
                    if tags:
                        for key, value in tags.items():
                            scope.set_tag(key, value)
                    
                    if context:
                        for key, value in context.items():
                            scope.set_context(key, value)
                    
                    scope.set_context("function", {
                        "name": func.__name__,
                        "module": func.__module__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    })
                    
                    sentry_sdk.capture_exception(e)
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
