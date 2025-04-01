from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ArchitectureMetricsBase(BaseModel):
    """Base model for architecture metrics."""
    timestamp: str = Field(..., description="ISO timestamp of when metrics were collected")


class CrossLayerMetrics(BaseModel):
    """Model for cross-layer call metrics."""
    calls: Dict[str, int] = Field({}, description="Count of calls between layers")
    errors: Dict[str, int] = Field({}, description="Count of errors between layers")
    timing_avg_ms: Dict[str, float] = Field({}, description="Average timing in milliseconds for calls between layers")


class LayerComponentCount(BaseModel):
    """Model for component counts by layer."""
    collection: int = Field(0, description="Number of components in the collection layer")
    processing: int = Field(0, description="Number of components in the processing layer")
    storage: int = Field(0, description="Number of components in the storage layer")
    api: int = Field(0, description="Number of components in the API layer")
    scheduled: int = Field(0, description="Number of components in the scheduled layer")
    consumer: int = Field(0, description="Number of components in the consumer layer")


class ArchitectureInfo(BaseModel):
    """Model for architecture information."""
    layer_counts: Dict[str, int] = Field({}, description="Count of components by layer")
    total_components: int = Field(0, description="Total number of tagged components")


class ArchitectureMetrics(ArchitectureMetricsBase):
    """Model for architecture metrics response."""
    runtime_metrics: Dict[str, Any] = Field({}, description="Runtime metrics collected from the system")
    architecture_info: ArchitectureInfo = Field(..., description="Information about the architecture")


class DiagnosticResult(BaseModel):
    """Model for a diagnostic script result."""
    success: bool = Field(..., description="Whether the diagnostic succeeded")
    script: str = Field(..., description="Name of the diagnostic script")
    results: Optional[Dict[str, Any]] = Field(None, description="Results from the diagnostic")
    stdout: Optional[str] = Field(None, description="Standard output from the script")
    stderr: Optional[str] = Field(None, description="Standard error from the script")
    exit_code: Optional[int] = Field(None, description="Exit code from the script")
    error: Optional[str] = Field(None, description="Error message, if any")


class AllDiagnosticsResult(BaseModel):
    """Model for the result of running all diagnostics."""
    success: bool = Field(..., description="Whether all diagnostics succeeded")
    timestamp: str = Field(..., description="ISO timestamp of when diagnostics were run")
    results: Dict[str, DiagnosticResult] = Field(..., description="Results from each diagnostic script")


class DiagnosticHistory(BaseModel):
    """Model for diagnostic history entries."""
    filename: str = Field(..., description="Name of the diagnostic results file")
    timestamp: str = Field(..., description="ISO timestamp of when the diagnostic was run")
    type: str = Field(..., description="Type of diagnostic")
    summary: Dict[str, Any] = Field(..., description="Summary of diagnostic results")


class DiagnosticSummary(BaseModel):
    """Model for summarized diagnostic results."""
    architecture_validation: Optional[Dict[str, Any]] = Field(None, description="Architecture validation results")
    property_tracking: Optional[Dict[str, Any]] = Field(None, description="Property tracking results")
    last_updated: Dict[str, Optional[str]] = Field(..., description="Timestamps of when each test was last run")


class HealthIndicator(BaseModel):
    """Model for system health indicators."""
    overall: str = Field(..., description="Overall health status (healthy, warning, unhealthy, unknown)")
    layers: Dict[str, str] = Field({}, description="Health status by layer")
    cross_layer_calls: str = Field(..., description="Health status of cross-layer calls")
    property_tracking: str = Field(..., description="Health status of property tracking")


class MetricsSaveResult(BaseModel):
    """Model for the result of saving metrics."""
    success: bool = Field(..., description="Whether metrics were successfully saved")
    filepath: Optional[str] = Field(None, description="Path to the saved metrics file")
    timestamp: Optional[str] = Field(None, description="Timestamp of the saved metrics")
    error: Optional[str] = Field(None, description="Error message, if any")