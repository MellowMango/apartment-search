"""
Production configuration for Lynnapse deployment.

Optimized settings for production environments including logging,
monitoring, performance tuning, and security configurations.
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class ProductionConfig:
    """Production configuration settings."""
    
    # Environment
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    
    # Performance Settings - Optimized for production workloads
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    rate_limit_delay: float = 1.0
    
    # Advanced Performance Tuning
    connection_pool_size: int = 20
    keep_alive_timeout: int = 30
    socket_timeout: int = 10
    read_timeout: int = 25
    
    # Memory Management - Production-optimized
    max_memory_mb: int = 400
    gc_threshold: int = 1000
    batch_processing_size: int = 50
    memory_check_interval: int = 60  # seconds
    force_gc_threshold_mb: int = 350  # Force GC when memory exceeds this
    
    # Faculty Processing Optimization
    faculty_batch_size: int = 25
    max_faculty_per_university: int = 500
    enable_progress_caching: bool = True
    cache_processed_results: bool = True
    result_cache_ttl: int = 3600  # 1 hour
    
    # Database Configuration
    mongodb_url: str = field(default_factory=lambda: os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    mongodb_database: str = field(default_factory=lambda: os.getenv("MONGODB_DATABASE", "lynnapse_prod"))
    mongodb_pool_size: int = 10
    mongodb_timeout_ms: int = 30000
    mongodb_max_idle_time_ms: int = 60000
    mongodb_heartbeat_frequency_ms: int = 10000
    
    # External API Configuration
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    bing_api_key: Optional[str] = field(default_factory=lambda: os.getenv("BING_API_KEY"))
    enable_ai_assistance: bool = False  # Disabled by default in production
    ai_cost_limit_per_session: float = 5.0  # $5 limit per session
    ai_cost_limit_per_faculty: float = 0.05  # $0.05 per faculty
    ai_timeout_seconds: int = 30
    
    # Security Settings
    user_agent: str = "Lynnapse Academic Scraper 1.0 (Research Purpose)"
    respect_robots_txt: bool = True
    request_headers: Dict[str, str] = field(default_factory=lambda: {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    
    # Advanced Security
    allowed_domains: List[str] = field(default_factory=lambda: ["*.edu", "*.ac.uk", "*.ac.*", "scholar.google.com"])
    blocked_domains: List[str] = field(default_factory=lambda: ["facebook.com", "twitter.com", "instagram.com"])
    max_redirect_hops: int = 5
    ssl_verify: bool = True
    
    # Monitoring & Logging
    enable_structured_logging: bool = True
    log_format: str = "json"
    log_file_path: Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE_PATH"))
    enable_metrics_collection: bool = True
    metrics_export_interval: int = 60  # seconds
    
    # Advanced Monitoring
    enable_performance_tracking: bool = True
    track_memory_usage: bool = True
    track_processing_times: bool = True
    track_error_rates: bool = True
    alert_on_memory_threshold: bool = True
    alert_memory_threshold_mb: int = 350
    
    # Health Check Configuration
    health_check_enabled: bool = True
    health_check_port: int = 8001
    health_check_timeout: int = 5
    health_check_interval: int = 30
    
    # Comprehensive Health Checks
    enable_database_health_check: bool = True
    enable_memory_health_check: bool = True
    enable_disk_health_check: bool = True
    enable_network_health_check: bool = True
    health_check_failure_threshold: int = 3
    
    # Data Storage
    output_directory: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "/data/lynnapse"))
    backup_enabled: bool = True
    backup_retention_days: int = 30
    compress_output_files: bool = True
    enable_output_versioning: bool = True
    
    # University-Specific Settings - Optimized delays
    university_request_delay: Dict[str, float] = field(default_factory=lambda: {
        "default": 1.0,
        "stanford.edu": 2.0,  # Be extra respectful
        "mit.edu": 2.0,
        "harvard.edu": 2.0,
        "cmu.edu": 1.5,
        "berkeley.edu": 1.5,
        "yale.edu": 2.0,
        "princeton.edu": 2.0
    })
    
    # Link Processing Configuration - Production optimized
    link_validation_timeout: int = 10
    max_link_candidates: int = 50
    quality_score_threshold: float = 0.5
    social_media_replacement_enabled: bool = True
    enable_link_prefetching: bool = True
    link_cache_size: int = 1000
    
    # Error Handling & Recovery
    enable_auto_recovery: bool = True
    max_consecutive_failures: int = 5
    failure_backoff_multiplier: float = 2.0
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 10
    circuit_breaker_timeout: int = 300  # 5 minutes
    
    # Performance Benchmarks & Targets
    target_faculty_per_second: float = 5.0
    target_memory_per_faculty_mb: float = 4.0
    target_success_rate: float = 0.95
    max_processing_time_per_faculty: float = 10.0  # seconds
    
    @classmethod
    def from_environment(cls) -> "ProductionConfig":
        """Create production config from environment variables."""
        return cls(
            environment=os.getenv("ENVIRONMENT", "production"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            
            # Performance
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "1.0")),
            
            # Advanced Performance
            connection_pool_size=int(os.getenv("CONNECTION_POOL_SIZE", "20")),
            keep_alive_timeout=int(os.getenv("KEEP_ALIVE_TIMEOUT", "30")),
            
            # Memory
            max_memory_mb=int(os.getenv("MAX_MEMORY_MB", "400")),
            batch_processing_size=int(os.getenv("BATCH_SIZE", "50")),
            force_gc_threshold_mb=int(os.getenv("FORCE_GC_THRESHOLD_MB", "350")),
            
            # Faculty Processing
            faculty_batch_size=int(os.getenv("FACULTY_BATCH_SIZE", "25")),
            max_faculty_per_university=int(os.getenv("MAX_FACULTY_PER_UNIVERSITY", "500")),
            
            # Database
            mongodb_pool_size=int(os.getenv("MONGODB_POOL_SIZE", "10")),
            mongodb_timeout_ms=int(os.getenv("MONGODB_TIMEOUT_MS", "30000")),
            
            # AI Configuration
            enable_ai_assistance=os.getenv("ENABLE_AI_ASSISTANCE", "false").lower() == "true",
            ai_cost_limit_per_session=float(os.getenv("AI_COST_LIMIT", "5.0")),
            ai_cost_limit_per_faculty=float(os.getenv("AI_COST_PER_FACULTY", "0.05")),
            
            # Monitoring
            enable_structured_logging=os.getenv("STRUCTURED_LOGGING", "true").lower() == "true",
            enable_metrics_collection=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            enable_performance_tracking=os.getenv("PERFORMANCE_TRACKING", "true").lower() == "true",
            
            # Health checks
            health_check_enabled=os.getenv("HEALTH_CHECK_ENABLED", "true").lower() == "true",
            health_check_port=int(os.getenv("HEALTH_CHECK_PORT", "8001")),
            
            # Error handling
            enable_auto_recovery=os.getenv("AUTO_RECOVERY", "true").lower() == "true",
            enable_circuit_breaker=os.getenv("CIRCUIT_BREAKER", "true").lower() == "true",
        )
    
    def get_university_delay(self, domain: str) -> float:
        """Get appropriate delay for specific university domain."""
        for uni_domain, delay in self.university_request_delay.items():
            if uni_domain in domain:
                return delay
        return self.university_request_delay["default"]
    
    def validate(self) -> None:
        """Validate production configuration."""
        errors = []
        
        # Check required settings
        if self.environment == "production" and self.debug:
            errors.append("Debug mode should be disabled in production")
        
        if self.max_concurrent_requests < 1:
            errors.append("max_concurrent_requests must be at least 1")
        
        if self.request_timeout_seconds < 5:
            errors.append("request_timeout_seconds should be at least 5 seconds")
        
        if self.enable_ai_assistance and not self.openai_api_key:
            errors.append("OpenAI API key required when AI assistance is enabled")
        
        if self.ai_cost_limit_per_session < 0:
            errors.append("AI cost limit must be non-negative")
        
        # Check memory limits
        if self.max_memory_mb < 100:
            errors.append("max_memory_mb should be at least 100MB")
        
        if self.force_gc_threshold_mb >= self.max_memory_mb:
            errors.append("force_gc_threshold_mb should be less than max_memory_mb")
        
        # Check performance targets
        if self.target_faculty_per_second <= 0:
            errors.append("target_faculty_per_second must be positive")
        
        if self.target_success_rate < 0 or self.target_success_rate > 1:
            errors.append("target_success_rate must be between 0 and 1")
        
        # Validate batch sizes
        if self.batch_processing_size < 1:
            errors.append("batch_processing_size must be at least 1")
        
        if self.faculty_batch_size < 1:
            errors.append("faculty_batch_size must be at least 1")
        
        # Validate database configuration
        if not self.mongodb_url:
            errors.append("MongoDB URL is required")
        
        if self.mongodb_pool_size < 1:
            errors.append("mongodb_pool_size must be at least 1")
        
        # Validate output directory
        output_path = Path(self.output_directory)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create output directory: {e}")
        
        # Validate health check configuration
        if self.health_check_enabled:
            if self.health_check_port < 1024 or self.health_check_port > 65535:
                errors.append("health_check_port must be between 1024 and 65535")
        
        # Validate circuit breaker configuration
        if self.enable_circuit_breaker:
            if self.circuit_breaker_threshold < 1:
                errors.append("circuit_breaker_threshold must be at least 1")
            if self.circuit_breaker_timeout < 1:
                errors.append("circuit_breaker_timeout must be at least 1")
        
        if errors:
            raise ValueError(f"Production configuration errors: {'; '.join(errors)}")
    
    def get_performance_targets(self) -> Dict[str, float]:
        """Get performance targets for monitoring."""
        return {
            "faculty_per_second_min": self.target_faculty_per_second,
            "memory_per_faculty_max_mb": self.target_memory_per_faculty_mb,
            "success_rate_min": self.target_success_rate,
            "processing_time_per_faculty_max_sec": self.max_processing_time_per_faculty,
            "memory_usage_max_mb": self.max_memory_mb,
            "concurrent_requests_max": self.max_concurrent_requests
        }
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get resource limits for deployment."""
        return {
            "memory_limit_mb": self.max_memory_mb,
            "cpu_limit": "1.0",  # 1 CPU core
            "disk_space_gb": 10,  # 10GB disk space
            "network_connections": self.max_concurrent_requests * 2,
            "file_descriptors": 1024,
            "processes": 1
        }


def setup_production_logging(config: ProductionConfig) -> None:
    """Set up production logging configuration."""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    if config.enable_structured_logging:
        # Structured JSON logging for production
        import json
        from datetime import datetime
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                    "environment": config.environment
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                
                # Add performance metrics if available
                if hasattr(record, 'performance_metrics'):
                    log_entry["performance"] = record.performance_metrics
                
                # Add extra fields
                for key, value in record.__dict__.items():
                    if key not in ["name", "msg", "args", "levelname", "levelno", 
                                 "pathname", "filename", "module", "lineno", 
                                 "funcName", "created", "msecs", "relativeCreated",
                                 "thread", "threadName", "processName", "process",
                                 "message", "exc_info", "exc_text", "stack_info"]:
                        log_entry[key] = value
                
                return json.dumps(log_entry)
        
        formatter = JSONFormatter()
    else:
        # Standard logging format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if config.log_file_path:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            config.log_file_path,
            maxBytes=100*1024*1024,  # 100MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def setup_production_monitoring(config: ProductionConfig) -> Dict[str, Any]:
    """Set up production monitoring and metrics collection."""
    monitoring_config = {
        "enabled": config.enable_metrics_collection,
        "export_interval": config.metrics_export_interval,
        "performance_tracking": config.enable_performance_tracking,
        "memory_tracking": config.track_memory_usage,
        "error_tracking": config.track_error_rates,
        "metrics": {
            # Processing metrics
            "faculty_processed_total": 0,
            "faculty_per_second": 0.0,
            "processing_time_avg_seconds": 0.0,
            "batch_processing_time_seconds": 0.0,
            
            # Link metrics
            "links_validated_total": 0,
            "social_media_links_found": 0,
            "social_media_replacements_successful": 0,
            "link_validation_success_rate": 0.0,
            
            # API metrics
            "api_calls_total": 0,
            "api_call_success_rate": 0.0,
            "api_cost_total": 0.0,
            "ai_assistance_calls": 0,
            
            # System metrics
            "memory_usage_mb": 0,
            "memory_peak_mb": 0,
            "memory_per_faculty_mb": 0.0,
            "cpu_usage_percent": 0.0,
            "disk_usage_percent": 0.0,
            
            # Error metrics
            "errors_total": 0,
            "error_rate": 0.0,
            "timeout_errors": 0,
            "network_errors": 0,
            "validation_errors": 0,
            
            # Performance targets
            "target_compliance": {
                "faculty_per_second": True,
                "memory_usage": True,
                "success_rate": True,
                "processing_time": True
            }
        },
        "alerts": {
            "enabled": config.alert_on_memory_threshold,
            "memory_threshold_mb": config.alert_memory_threshold_mb,
            "error_rate_threshold": 0.1,  # 10% error rate threshold
            "performance_degradation_threshold": 0.5  # 50% below target
        }
    }
    
    return monitoring_config


def create_health_check_server(config: ProductionConfig):
    """Create comprehensive health check server for production deployment."""
    if not config.health_check_enabled:
        return None
    
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import asyncio
    import uvicorn
    import psutil
    
    health_app = FastAPI(title="Lynnapse Health Check", version="1.0.0")
    
    @health_app.get("/health")
    async def health_check():
        """Comprehensive health check endpoint."""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "environment": config.environment,
                "checks": {}
            }
            
            # Database health check
            if config.enable_database_health_check:
                health_status["checks"]["database"] = await check_database_health(config)
            
            # Memory health check
            if config.enable_memory_health_check:
                health_status["checks"]["memory"] = check_memory_health(config)
            
            # Disk health check
            if config.enable_disk_health_check:
                health_status["checks"]["disk"] = check_disk_health(config)
            
            # Network health check
            if config.enable_network_health_check:
                health_status["checks"]["network"] = await check_network_health(config)
            
            # Overall health determination
            all_healthy = all(
                check.get("status") == "healthy" 
                for check in health_status["checks"].values()
            )
            
            if not all_healthy:
                health_status["status"] = "unhealthy"
                status_code = 503
            else:
                status_code = 200
            
            return JSONResponse(content=health_status, status_code=status_code)
            
        except Exception as e:
            error_response = {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
            return JSONResponse(content=error_response, status_code=500)
    
    @health_app.get("/metrics")
    async def metrics():
        """Comprehensive metrics endpoint for monitoring systems."""
        try:
            metrics_data = get_current_metrics(config)
            return JSONResponse(content=metrics_data)
        except Exception as e:
            error_response = {
                "error": f"Failed to collect metrics: {str(e)}",
                "timestamp": time.time()
            }
            return JSONResponse(content=error_response, status_code=500)
    
    @health_app.get("/performance")
    async def performance_metrics():
        """Performance-specific metrics endpoint."""
        try:
            performance_data = get_performance_metrics(config)
            return JSONResponse(content=performance_data)
        except Exception as e:
            error_response = {
                "error": f"Failed to collect performance metrics: {str(e)}",
                "timestamp": time.time()
            }
            return JSONResponse(content=error_response, status_code=500)
    
    return health_app


async def check_database_health(config: ProductionConfig) -> Dict[str, Any]:
    """Check database connectivity and health."""
    try:
        from lynnapse.db.mongodb import get_database
        
        start_time = time.time()
        db = get_database(config.mongodb_url, config.mongodb_database)
        
        # Simple ping operation
        await db.command("ping")
        response_time = (time.time() - start_time) * 1000  # ms
        
        # Check collection stats
        collections = await db.list_collection_names()
        
        return {
            "status": "healthy",
            "message": "Database connection successful",
            "response_time_ms": response_time,
            "collections_found": len(collections),
            "url": config.mongodb_url,
            "database": config.mongodb_database
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "url": config.mongodb_url
        }


def check_memory_health(config: ProductionConfig) -> Dict[str, Any]:
    """Check memory usage health."""
    try:
        import psutil
        
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        memory_percent = process.memory_percent()
        
        # System memory
        system_memory = psutil.virtual_memory()
        system_memory_mb = system_memory.used / 1024 / 1024
        
        status = "healthy"
        if memory_mb > config.alert_memory_threshold_mb:
            status = "warning"
        if memory_mb > config.max_memory_mb:
            status = "unhealthy"
        
        return {
            "status": status,
            "process_memory_mb": memory_mb,
            "process_memory_percent": memory_percent,
            "system_memory_mb": system_memory_mb,
            "system_memory_percent": system_memory.percent,
            "memory_limit_mb": config.max_memory_mb,
            "memory_threshold_mb": config.alert_memory_threshold_mb,
            "memory_available_mb": system_memory.available / 1024 / 1024
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Memory check failed: {str(e)}"
        }


def check_disk_health(config: ProductionConfig) -> Dict[str, Any]:
    """Check disk space health."""
    try:
        import shutil
        
        output_path = Path(config.output_directory)
        total, used, free = shutil.disk_usage(output_path)
        
        free_gb = free / (1024**3)
        used_gb = used / (1024**3)
        total_gb = total / (1024**3)
        free_percentage = (free / total) * 100
        
        status = "healthy"
        if free_percentage < 20:
            status = "warning"
        if free_percentage < 5:
            status = "unhealthy"
        
        return {
            "status": status,
            "free_space_gb": free_gb,
            "used_space_gb": used_gb,
            "total_space_gb": total_gb,
            "free_percentage": free_percentage,
            "output_directory": str(output_path)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Disk check failed: {str(e)}"
        }


async def check_network_health(config: ProductionConfig) -> Dict[str, Any]:
    """Check network connectivity health."""
    try:
        import aiohttp
        import asyncio
        
        # Test connections to key services
        test_urls = [
            "https://www.google.com",
            "https://scholar.google.com",
        ]
        
        if config.enable_ai_assistance and config.openai_api_key:
            test_urls.append("https://api.openai.com")
        
        async def test_url(url):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    start_time = time.time()
                    async with session.get(url) as response:
                        response_time = (time.time() - start_time) * 1000
                        return {
                            "url": url,
                            "status": "healthy" if response.status < 400 else "unhealthy",
                            "status_code": response.status,
                            "response_time_ms": response_time
                        }
            except Exception as e:
                return {
                    "url": url,
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Test all URLs concurrently
        results = await asyncio.gather(*[test_url(url) for url in test_urls])
        
        healthy_count = sum(1 for result in results if result["status"] == "healthy")
        
        overall_status = "healthy" if healthy_count == len(results) else "warning"
        if healthy_count == 0:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "tests_passed": healthy_count,
            "tests_total": len(results),
            "test_results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Network check failed: {str(e)}"
        }


def get_current_metrics(config: ProductionConfig) -> Dict[str, Any]:
    """Get current comprehensive system metrics."""
    try:
        import psutil
        
        process = psutil.Process()
        
        return {
            "timestamp": time.time(),
            "environment": config.environment,
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None,
                "boot_time": psutil.boot_time()
            },
            "process": {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0,
                "create_time": process.create_time(),
                "connections": len(process.connections()) if hasattr(process, 'connections') else 0
            },
            "configuration": {
                "max_concurrent_requests": config.max_concurrent_requests,
                "max_memory_mb": config.max_memory_mb,
                "ai_assistance_enabled": config.enable_ai_assistance,
                "batch_size": config.batch_processing_size,
                "faculty_batch_size": config.faculty_batch_size
            },
            "performance_targets": config.get_performance_targets()
        }
    except Exception as e:
        return {
            "error": f"Failed to collect metrics: {str(e)}",
            "timestamp": time.time()
        }


def get_performance_metrics(config: ProductionConfig) -> Dict[str, Any]:
    """Get performance-specific metrics."""
    try:
        import psutil
        
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Performance compliance checks
        targets = config.get_performance_targets()
        
        return {
            "timestamp": time.time(),
            "current_performance": {
                "memory_usage_mb": memory_mb,
                "cpu_usage_percent": process.cpu_percent(),
                "thread_count": process.num_threads(),
                "memory_efficiency": memory_mb < targets["memory_usage_max_mb"]
            },
            "targets": targets,
            "compliance": {
                "memory_within_limits": memory_mb < targets["memory_usage_max_mb"],
                "memory_threshold_ok": memory_mb < config.alert_memory_threshold_mb,
                "gc_threshold_ok": memory_mb < config.force_gc_threshold_mb
            },
            "recommendations": get_performance_recommendations(config, memory_mb)
        }
    except Exception as e:
        return {
            "error": f"Failed to collect performance metrics: {str(e)}",
            "timestamp": time.time()
        }


def get_performance_recommendations(config: ProductionConfig, current_memory_mb: float) -> List[str]:
    """Get performance optimization recommendations."""
    recommendations = []
    
    if current_memory_mb > config.alert_memory_threshold_mb:
        recommendations.append("Memory usage is high - consider reducing batch size or concurrent requests")
    
    if current_memory_mb > config.force_gc_threshold_mb:
        recommendations.append("Memory usage critical - force garbage collection recommended")
    
    if config.max_concurrent_requests > 15:
        recommendations.append("High concurrency - monitor for diminishing returns")
    
    if config.batch_processing_size > 100:
        recommendations.append("Large batch size - may impact memory usage")
    
    if not config.enable_performance_tracking:
        recommendations.append("Enable performance tracking for better optimization")
    
    return recommendations


# Global production configuration instance
_production_config: Optional[ProductionConfig] = None


def get_production_config() -> ProductionConfig:
    """Get the global production configuration instance."""
    global _production_config
    
    if _production_config is None:
        _production_config = ProductionConfig.from_environment()
        _production_config.validate()
        
        # Set up logging
        setup_production_logging(_production_config)
        
        logging.getLogger(__name__).info(
            "Production configuration loaded",
            extra={
                "environment": _production_config.environment,
                "max_concurrent": _production_config.max_concurrent_requests,
                "memory_limit_mb": _production_config.max_memory_mb,
                "ai_enabled": _production_config.enable_ai_assistance,
                "performance_targets": _production_config.get_performance_targets()
            }
        )
    
    return _production_config


def initialize_production_environment() -> ProductionConfig:
    """Initialize complete production environment."""
    config = get_production_config()
    
    # Set up monitoring
    monitoring_config = setup_production_monitoring(config)
    
    # Create output directory
    output_path = Path(config.output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Set up health check server if enabled
    if config.health_check_enabled:
        health_app = create_health_check_server(config)
        # Health check server would typically be started in a separate process
    
    # Set up garbage collection tuning
    import gc
    gc.set_threshold(config.gc_threshold, config.gc_threshold // 10, config.gc_threshold // 100)
    
    # Set up memory monitoring if enabled
    if config.track_memory_usage:
        setup_memory_monitoring(config)
    
    logging.getLogger(__name__).info(
        "Production environment initialized",
        extra={
            "output_directory": str(output_path),
            "health_check_enabled": config.health_check_enabled,
            "monitoring_enabled": config.enable_metrics_collection,
            "performance_tracking": config.enable_performance_tracking,
            "memory_monitoring": config.track_memory_usage,
            "resource_limits": config.get_resource_limits()
        }
    )
    
    return config


def setup_memory_monitoring(config: ProductionConfig) -> None:
    """Set up memory monitoring and alerting."""
    import threading
    import psutil
    
    def memory_monitor():
        """Background memory monitoring thread."""
        while True:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                if memory_mb > config.force_gc_threshold_mb:
                    import gc
                    gc.collect()
                    logging.getLogger(__name__).warning(
                        "Memory threshold exceeded - forced garbage collection",
                        extra={"memory_mb": memory_mb, "threshold_mb": config.force_gc_threshold_mb}
                    )
                
                if memory_mb > config.alert_memory_threshold_mb:
                    logging.getLogger(__name__).warning(
                        "Memory usage high",
                        extra={"memory_mb": memory_mb, "alert_threshold_mb": config.alert_memory_threshold_mb}
                    )
                
                time.sleep(config.memory_check_interval)
                
            except Exception as e:
                logging.getLogger(__name__).error(f"Memory monitoring error: {e}")
                time.sleep(config.memory_check_interval)
    
    # Start memory monitoring thread
    if config.track_memory_usage:
        monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
        monitor_thread.start()
        logging.getLogger(__name__).info("Memory monitoring started") 