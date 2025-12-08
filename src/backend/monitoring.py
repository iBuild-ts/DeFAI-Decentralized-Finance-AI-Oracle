"""
Monitoring and Health Checks for DeFAI Oracle
Tracks system health, performance, and alerts
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import time
import psutil
import asyncio


class HealthChecker:
    """Monitors system health"""
    
    def __init__(self):
        self.logger = logger.bind(component="HealthChecker")
        self.start_time = datetime.now()
        self.last_check = datetime.now()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Uptime
            uptime = datetime.now() - self.start_time
            
            # Determine health status
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 80:
                status = "warning"
            if cpu_percent > 95 or memory.percent > 95:
                status = "critical"
            
            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": int(uptime.total_seconds()),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                },
                "memory": {
                    "percent": memory.percent,
                    "available_mb": memory.available // (1024 * 1024),
                    "total_mb": memory.total // (1024 * 1024),
                },
                "disk": {
                    "percent": disk.percent,
                    "free_gb": disk.free // (1024 * 1024 * 1024),
                    "total_gb": disk.total // (1024 * 1024 * 1024),
                },
            }
        
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
    
    def get_api_health(self) -> Dict[str, Any]:
        """Get API health status"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "0.1.0",
            "uptime_seconds": int((datetime.now() - self.start_time).total_seconds()),
        }


class PerformanceMonitor:
    """Monitors API performance"""
    
    def __init__(self):
        self.logger = logger.bind(component="PerformanceMonitor")
        self.request_times: Dict[str, List[float]] = {}
        self.request_counts: Dict[str, int] = {}
    
    def record_request(self, endpoint: str, duration_ms: float):
        """Record request performance"""
        if endpoint not in self.request_times:
            self.request_times[endpoint] = []
            self.request_counts[endpoint] = 0
        
        self.request_times[endpoint].append(duration_ms)
        self.request_counts[endpoint] += 1
        
        # Keep only last 1000 requests
        if len(self.request_times[endpoint]) > 1000:
            self.request_times[endpoint] = self.request_times[endpoint][-1000:]
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for an endpoint"""
        if endpoint not in self.request_times or not self.request_times[endpoint]:
            return {
                "endpoint": endpoint,
                "requests": 0,
            }
        
        times = self.request_times[endpoint]
        
        return {
            "endpoint": endpoint,
            "requests": self.request_counts[endpoint],
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": sorted(times)[int(len(times) * 0.95)],
            "p99_ms": sorted(times)[int(len(times) * 0.99)],
        }
    
    def get_all_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all endpoints"""
        return [self.get_endpoint_stats(endpoint) for endpoint in self.request_times.keys()]


class AlertSystem:
    """Alert system for monitoring"""
    
    def __init__(self):
        self.logger = logger.bind(component="AlertSystem")
        self.alerts: List[Dict[str, Any]] = []
        self.alert_handlers: List[callable] = []
    
    def register_handler(self, handler: callable):
        """Register an alert handler"""
        self.alert_handlers.append(handler)
    
    async def trigger_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """Trigger an alert"""
        alert = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        self.logger.warning(f"Alert: {alert_type} - {message}")
        
        # Call handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts[-limit:]
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []


class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self):
        self.logger = logger.bind(component="MetricsCollector")
        self.metrics: Dict[str, Any] = {}
        self.start_time = datetime.now()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or {},
        })
        
        # Keep only last 1000 values
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metric_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return {"metric": name, "samples": 0}
        
        values = [m["value"] for m in self.metrics[name]]
        
        return {
            "metric": name,
            "samples": len(values),
            "current": values[-1],
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            name: self.get_metric_stats(name)
            for name in self.metrics.keys()
        }


# Global instances
health_checker: Optional[HealthChecker] = None
performance_monitor: Optional[PerformanceMonitor] = None
alert_system: Optional[AlertSystem] = None
metrics_collector: Optional[MetricsCollector] = None


def initialize_monitoring():
    """Initialize monitoring system"""
    global health_checker, performance_monitor, alert_system, metrics_collector
    
    health_checker = HealthChecker()
    performance_monitor = PerformanceMonitor()
    alert_system = AlertSystem()
    metrics_collector = MetricsCollector()
    
    logger.info("Monitoring system initialized")


def get_health_checker() -> HealthChecker:
    """Get health checker instance"""
    return health_checker


def get_performance_monitor() -> PerformanceMonitor:
    """Get performance monitor instance"""
    return performance_monitor


def get_alert_system() -> AlertSystem:
    """Get alert system instance"""
    return alert_system


def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector instance"""
    return metrics_collector
