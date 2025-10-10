"""
DevOps Service Client Library

Provides easy integration with DevOps service for all microservices.
Handles incident reporting, SLO monitoring, and metrics collection.
"""

import httpx
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SLIType(str, Enum):
    """Service Level Indicator types"""
    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


class DevOpsClient:
    """
    DevOps Service Client
    
    Integrates with DevOps service for incident management,
    SLO monitoring, and observability.
    """
    
    def __init__(self, devops_url: str = "http://devops-service:8100"):
        self.devops_url = devops_url
        self.service_name = None
        self.timeout = 10.0
    
    def configure(self, service_name: str):
        """Configure client with service name"""
        self.service_name = service_name
        logger.info(f"DevOps client configured for service: {service_name}")
    
    async def report_incident(
        self,
        title: str,
        description: str,
        severity: IncidentSeverity,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:
        """
        Report an incident to DevOps service
        
        Args:
            title: Incident title
            description: Detailed description
            severity: Incident severity level
            metadata: Additional context
        
        Returns:
            Incident details or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.devops_url}/api/v1/incidents",
                    json={
                        "title": title,
                        "description": description,
                        "severity": severity.value,
                        "service": self.service_name or "unknown",
                        "metadata": metadata or {}
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    incident = response.json()
                    logger.info(f"Incident reported: {incident.get('incident_id')}")
                    return incident
                else:
                    logger.error(f"Failed to report incident: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error reporting incident: {e}")
            return None
    
    async def check_slo_compliance(
        self,
        sli_type: SLIType
    ) -> Optional[Dict]:
        """
        Check SLO compliance for this service
        
        Args:
            sli_type: Type of SLI to check
        
        Returns:
            SLO status or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.devops_url}/api/v1/slo/{self.service_name}/status",
                    params={"sli_type": sli_type.value},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to check SLO: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error checking SLO: {e}")
            return None
    
    async def query_metrics(self, query: str) -> Optional[Dict]:
        """
        Query Prometheus metrics
        
        Args:
            query: PromQL query string
        
        Returns:
            Metrics data or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.devops_url}/api/v1/metrics/query",
                    params={"query": query},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to query metrics: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error querying metrics: {e}")
            return None
    
    async def trigger_canary_deployment(
        self,
        new_version: str,
        canary_steps: list = None
    ) -> Optional[Dict]:
        """
        Trigger canary deployment for this service
        
        Args:
            new_version: New version to deploy
            canary_steps: Traffic percentage steps
        
        Returns:
            Deployment details or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.devops_url}/api/v1/deployments/canary",
                    json={
                        "service_name": self.service_name,
                        "new_version": new_version,
                        "canary_steps": canary_steps or [10, 25, 50, 75, 100],
                        "analysis_interval": 300,
                        "success_threshold": 99.0
                    }
                )
                
                if response.status_code == 200:
                    deployment = response.json()
                    logger.info(f"Canary deployment triggered: {deployment.get('deployment_id')}")
                    return deployment
                else:
                    logger.error(f"Failed to trigger deployment: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error triggering deployment: {e}")
            return None
    
    async def get_deployment_status(self) -> Optional[Dict]:
        """Get current deployment status for this service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.devops_url}/api/v1/deployments/{self.service_name}/status",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting deployment status: {e}")
            return None


# Singleton instance
_devops_client: Optional[DevOpsClient] = None


def get_devops_client(devops_url: str = "http://devops-service:8100") -> DevOpsClient:
    """Get or create DevOps client instance"""
    global _devops_client
    if _devops_client is None:
        _devops_client = DevOpsClient(devops_url)
    return _devops_client


# Convenience decorators
def report_errors_as_incidents(severity: IncidentSeverity = IncidentSeverity.HIGH):
    """
    Decorator to automatically report function errors as incidents
    
    Usage:
        @report_errors_as_incidents(severity=IncidentSeverity.CRITICAL)
        async def critical_operation():
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                client = get_devops_client()
                await client.report_incident(
                    title=f"Error in {func.__name__}",
                    description=str(e),
                    severity=severity,
                    metadata={
                        "function": func.__name__,
                        "error_type": type(e).__name__,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                raise
        return wrapper
    return decorator
