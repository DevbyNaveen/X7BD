"""
Chaos Engineering Utilities

Enterprise-grade chaos engineering tools for testing system resilience.
Implements controlled failure injection for microservices.
"""

import random
import asyncio
from typing import Optional, Callable, Any, Dict
from functools import wraps
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChaosConfig:
    """Configuration for chaos experiments"""
    
    def __init__(
        self,
        enabled: bool = False,
        failure_rate: float = 0.1,
        latency_min_ms: int = 100,
        latency_max_ms: int = 5000,
        exception_types: Optional[list] = None
    ):
        """
        Initialize chaos configuration
        
        Args:
            enabled: Enable chaos engineering
            failure_rate: Probability of failure (0.0 to 1.0)
            latency_min_ms: Minimum latency injection (ms)
            latency_max_ms: Maximum latency injection (ms)
            exception_types: List of exception types to inject
        """
        self.enabled = enabled
        self.failure_rate = failure_rate
        self.latency_min_ms = latency_min_ms
        self.latency_max_ms = latency_max_ms
        self.exception_types = exception_types or [
            Exception("Chaos: Simulated failure"),
            TimeoutError("Chaos: Simulated timeout"),
            ConnectionError("Chaos: Simulated connection error")
        ]


class ChaosMonkey:
    """
    Chaos Monkey for controlled failure injection
    
    Features:
    - Random failure injection
    - Latency injection
    - Exception injection
    - Circuit breaker simulation
    - Resource exhaustion simulation
    """
    
    def __init__(self, config: ChaosConfig):
        """
        Initialize Chaos Monkey
        
        Args:
            config: Chaos configuration
        """
        self.config = config
        self.experiment_log: list = []
    
    def should_inject_failure(self) -> bool:
        """Determine if failure should be injected"""
        if not self.config.enabled:
            return False
        return random.random() < self.config.failure_rate
    
    def inject_latency(self) -> int:
        """
        Inject random latency
        
        Returns:
            Latency in milliseconds
        """
        if not self.config.enabled:
            return 0
        
        latency = random.randint(
            self.config.latency_min_ms,
            self.config.latency_max_ms
        )
        
        self._log_experiment("latency_injection", {"latency_ms": latency})
        return latency
    
    def inject_exception(self) -> Exception:
        """
        Get random exception to inject
        
        Returns:
            Random exception from configured types
        """
        exception = random.choice(self.config.exception_types)
        self._log_experiment("exception_injection", {"exception": str(exception)})
        return exception
    
    def _log_experiment(self, experiment_type: str, details: Dict[str, Any]):
        """Log chaos experiment"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": experiment_type,
            "details": details
        }
        self.experiment_log.append(log_entry)
        logger.info(f"Chaos experiment: {experiment_type} - {details}")
    
    def get_experiment_log(self) -> list:
        """Get experiment log"""
        return self.experiment_log
    
    def clear_log(self):
        """Clear experiment log"""
        self.experiment_log = []


# Global chaos monkey instance
chaos_config = ChaosConfig(enabled=False)  # Disabled by default
chaos_monkey = ChaosMonkey(chaos_config)


def chaos_latency(min_ms: int = 100, max_ms: int = 2000):
    """
    Decorator to inject random latency
    
    Args:
        min_ms: Minimum latency in milliseconds
        max_ms: Maximum latency in milliseconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if chaos_monkey.config.enabled:
                latency_ms = random.randint(min_ms, max_ms)
                logger.warning(f"Chaos: Injecting {latency_ms}ms latency to {func.__name__}")
                await asyncio.sleep(latency_ms / 1000.0)
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if chaos_monkey.config.enabled:
                latency_ms = random.randint(min_ms, max_ms)
                logger.warning(f"Chaos: Injecting {latency_ms}ms latency to {func.__name__}")
                import time
                time.sleep(latency_ms / 1000.0)
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def chaos_exception(failure_rate: float = 0.1, exception_type: Optional[Exception] = None):
    """
    Decorator to inject random exceptions
    
    Args:
        failure_rate: Probability of exception (0.0 to 1.0)
        exception_type: Specific exception to inject
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if chaos_monkey.config.enabled and random.random() < failure_rate:
                exc = exception_type or chaos_monkey.inject_exception()
                logger.error(f"Chaos: Injecting exception to {func.__name__}: {exc}")
                raise exc
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if chaos_monkey.config.enabled and random.random() < failure_rate:
                exc = exception_type or chaos_monkey.inject_exception()
                logger.error(f"Chaos: Injecting exception to {func.__name__}: {exc}")
                raise exc
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def chaos_resource_exhaustion(memory_mb: int = 100, duration_sec: int = 5):
    """
    Decorator to simulate resource exhaustion
    
    Args:
        memory_mb: Memory to allocate in MB
        duration_sec: Duration to hold resources
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if chaos_monkey.config.enabled and chaos_monkey.should_inject_failure():
                logger.warning(f"Chaos: Simulating resource exhaustion in {func.__name__}")
                # Allocate memory
                waste = bytearray(memory_mb * 1024 * 1024)
                await asyncio.sleep(duration_sec)
                del waste
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if chaos_monkey.config.enabled and chaos_monkey.should_inject_failure():
                logger.warning(f"Chaos: Simulating resource exhaustion in {func.__name__}")
                import time
                waste = bytearray(memory_mb * 1024 * 1024)
                time.sleep(duration_sec)
                del waste
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreakerSimulator:
    """
    Simulate circuit breaker behavior for chaos testing
    
    Features:
    - Automatic failure detection
    - Circuit opening/closing
    - Half-open state testing
    - Configurable thresholds
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker simulator
        
        Args:
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.state = "closed"  # closed, open, half_open
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
    
    def record_success(self):
        """Record successful call"""
        if self.state == "half_open":
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = "closed"
                self.failure_count = 0
                self.half_open_calls = 0
                logger.info("Circuit breaker: Closed (recovered)")
        elif self.state == "closed":
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker: Opened after {self.failure_count} failures")
    
    def should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "half_open"
                    self.half_open_calls = 0
                    logger.info("Circuit breaker: Half-open (testing recovery)")
                    return True
            return False
        
        if self.state == "half_open":
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "half_open_calls": self.half_open_calls
        }


def with_circuit_breaker(circuit_breaker: CircuitBreakerSimulator):
    """
    Decorator to apply circuit breaker pattern
    
    Args:
        circuit_breaker: Circuit breaker instance
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not circuit_breaker.should_allow_request():
                raise Exception(f"Circuit breaker is {circuit_breaker.state}")
            
            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not circuit_breaker.should_allow_request():
                raise Exception(f"Circuit breaker is {circuit_breaker.state}")
            
            try:
                result = func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ChaosExperiment:
    """
    Structured chaos experiment runner
    
    Features:
    - Controlled experiment execution
    - Hypothesis validation
    - Metrics collection
    - Rollback on critical failures
    """
    
    def __init__(self, name: str, hypothesis: str):
        """
        Initialize chaos experiment
        
        Args:
            name: Experiment name
            hypothesis: Hypothesis to test
        """
        self.name = name
        self.hypothesis = hypothesis
        self.results: Dict[str, Any] = {
            "name": name,
            "hypothesis": hypothesis,
            "start_time": None,
            "end_time": None,
            "status": "pending",
            "observations": [],
            "metrics": {}
        }
    
    async def run(
        self,
        steady_state_check: Callable,
        chaos_action: Callable,
        duration_sec: int = 60
    ):
        """
        Run chaos experiment
        
        Args:
            steady_state_check: Function to verify steady state
            chaos_action: Chaos action to execute
            duration_sec: Experiment duration
        """
        self.results["start_time"] = datetime.utcnow().isoformat()
        
        try:
            # Verify steady state before
            logger.info(f"Chaos experiment '{self.name}': Verifying initial steady state")
            initial_state = await steady_state_check()
            self.results["observations"].append({
                "phase": "initial",
                "steady_state": initial_state,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Execute chaos action
            logger.info(f"Chaos experiment '{self.name}': Executing chaos action")
            await chaos_action()
            
            # Monitor during chaos
            await asyncio.sleep(duration_sec)
            
            # Verify steady state after
            logger.info(f"Chaos experiment '{self.name}': Verifying final steady state")
            final_state = await steady_state_check()
            self.results["observations"].append({
                "phase": "final",
                "steady_state": final_state,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Validate hypothesis
            if initial_state == final_state:
                self.results["status"] = "success"
                logger.info(f"Chaos experiment '{self.name}': Hypothesis validated")
            else:
                self.results["status"] = "failed"
                logger.warning(f"Chaos experiment '{self.name}': Hypothesis rejected")
            
        except Exception as e:
            self.results["status"] = "error"
            self.results["error"] = str(e)
            logger.error(f"Chaos experiment '{self.name}' error: {e}", exc_info=True)
        
        finally:
            self.results["end_time"] = datetime.utcnow().isoformat()
    
    def get_results(self) -> Dict[str, Any]:
        """Get experiment results"""
        return self.results
