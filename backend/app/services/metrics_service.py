"""
Metrics Service for Architecture Monitoring

This service provides functions to collect, analyze and serve architecture metrics
for monitoring system health and performance. It works with the diagnostic scripts
to create a cohesive view of the architecture's state.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess
import sys

from ..utils.monitoring import get_metrics, reset_metrics, save_metrics_to_file
from ..utils.architecture import get_all_tagged_classes, ArchitectureLayer

logger = logging.getLogger(__name__)

class MetricsService:
    """Service for collecting and analyzing architecture metrics."""
    
    def __init__(self):
        """Initialize the metrics service."""
        self.diagnostic_results_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../diagnostic_results")
        )
        os.makedirs(self.diagnostic_results_dir, exist_ok=True)
    
    async def get_architecture_metrics(self) -> Dict[str, Any]:
        """
        Get current architecture metrics.
        
        Returns:
            Dictionary containing all metrics about the architecture
        """
        # Get current runtime metrics
        current_metrics = get_metrics()
        
        # Get layer information
        layers_info = await self.get_layers_info()
        
        # Combine metrics
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "runtime_metrics": current_metrics,
            "architecture_info": layers_info
        }
        
        return metrics
    
    async def get_layers_info(self) -> Dict[str, Any]:
        """
        Get information about architecture layers.
        
        Returns:
            Dictionary with components by layer, interaction counts, etc.
        """
        # Get all tagged classes
        tagged_classes = get_all_tagged_classes()
        
        # Count components by layer
        layer_counts = {}
        for layer in ArchitectureLayer:
            layer_counts[layer.value] = len([cls for cls, l in tagged_classes if l == layer])
        
        return {
            "layer_counts": layer_counts,
            "total_components": sum(layer_counts.values())
        }
    
    async def get_latest_diagnostic_results(self) -> Dict[str, Any]:
        """
        Get the latest diagnostic results from all diagnostic scripts.
        
        Returns:
            Dictionary containing results from all diagnostic scripts
        """
        results = {}
        
        # Check for layer interactions test results
        layer_interactions_file = os.path.join(self.diagnostic_results_dir, "architecture_validation.json")
        if os.path.exists(layer_interactions_file):
            with open(layer_interactions_file, 'r') as f:
                results["architecture_validation"] = json.load(f)
        
        # Check for property tracking test results
        property_tracking_file = os.path.join(self.diagnostic_results_dir, "property_tracking_verification.json")
        if os.path.exists(property_tracking_file):
            with open(property_tracking_file, 'r') as f:
                results["property_tracking"] = json.load(f)
        
        # Add timestamps for when each test was last run
        results["last_updated"] = {
            "architecture_validation": self._get_file_timestamp(layer_interactions_file),
            "property_tracking": self._get_file_timestamp(property_tracking_file)
        }
        
        return results
    
    def _get_file_timestamp(self, filepath: str) -> Optional[str]:
        """Get the last modified timestamp of a file if it exists."""
        if os.path.exists(filepath):
            timestamp = datetime.fromtimestamp(os.path.getmtime(filepath))
            return timestamp.isoformat()
        return None
    
    async def run_diagnostic_script(self, script_name: str) -> Dict[str, Any]:
        """
        Run a diagnostic script and return the results.
        
        Args:
            script_name: Name of the script to run (without .py extension)
            
        Returns:
            Dictionary with the result status and any output
        """
        script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), f"../../../backend/scripts/{script_name}.py")
        )
        
        if not os.path.exists(script_path):
            return {
                "success": False,
                "error": f"Script {script_name}.py not found"
            }
        
        try:
            # Run the script asynchronously
            process = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Check for results file
            if script_name == "test_layer_interactions":
                result_file = os.path.join(self.diagnostic_results_dir, "architecture_validation.json")
            elif script_name == "verify_property_tracking":
                result_file = os.path.join(self.diagnostic_results_dir, "property_tracking_verification.json")
            elif script_name == "test_architecture_flow":
                result_file = os.path.join(self.diagnostic_results_dir, "architecture_validation.json")
            else:
                result_file = None
            
            # Load results if the file exists
            results = None
            if result_file and os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    results = json.load(f)
            
            return {
                "success": process.returncode == 0,
                "script": script_name,
                "stdout": stdout.decode(),
                "stderr": stderr.decode() if stderr else None,
                "results": results,
                "exit_code": process.returncode
            }
            
        except Exception as e:
            logger.error(f"Error running diagnostic script {script_name}: {e}")
            return {
                "success": False,
                "script": script_name,
                "error": str(e)
            }
    
    async def run_all_diagnostics(self) -> Dict[str, Any]:
        """
        Run all diagnostic scripts and return combined results.
        
        Returns:
            Dictionary with combined results from all scripts
        """
        scripts = [
            "test_layer_interactions",
            "verify_property_tracking",
            "test_architecture_flow"
        ]
        
        results = {}
        for script in scripts:
            results[script] = await self.run_diagnostic_script(script)
        
        # Overall success is True only if all scripts succeeded
        success = all(result.get("success", False) for result in results.values())
        
        return {
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }
    
    async def save_current_metrics(self) -> Dict[str, Any]:
        """
        Save current metrics to a file.
        
        Returns:
            Dictionary with the result status
        """
        try:
            # Generate timestamp for filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"architecture_metrics_{timestamp}.json"
            filepath = os.path.join(self.diagnostic_results_dir, filename)
            
            # Get metrics
            metrics = await self.get_architecture_metrics()
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            
            return {
                "success": True,
                "filepath": filepath,
                "timestamp": timestamp
            }
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_diagnostic_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get history of diagnostic runs.
        
        Args:
            limit: Maximum number of historical entries to return
            
        Returns:
            List of diagnostic results, sorted by date (newest first)
        """
        history = []
        
        # Check all json files in the diagnostic_results directory
        for filename in os.listdir(self.diagnostic_results_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.diagnostic_results_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Add metadata
                    timestamp = datetime.fromtimestamp(os.path.getmtime(filepath))
                    entry = {
                        "filename": filename,
                        "timestamp": timestamp.isoformat(),
                        "type": self._determine_file_type(filename),
                        "summary": self._extract_summary(data)
                    }
                    
                    history.append(entry)
                except Exception as e:
                    logger.warning(f"Error reading diagnostic file {filename}: {e}")
        
        # Sort by timestamp (newest first) and limit results
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history[:limit]
    
    def _determine_file_type(self, filename: str) -> str:
        """Determine the type of diagnostic file based on its name."""
        if "architecture_validation" in filename:
            return "architecture_validation"
        elif "property_tracking" in filename:
            return "property_tracking"
        elif "architecture_metrics" in filename:
            return "metrics"
        else:
            return "unknown"
    
    def _extract_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a summary from the diagnostic data."""
        summary = {
            "success": data.get("success", False)
        }
        
        # Add specific summaries based on file type
        if "results" in data:
            if isinstance(data["results"], dict):
                summary["tests"] = len(data["results"])
                summary["passed"] = sum(1 for result in data["results"].values() 
                                      if result is True or (isinstance(result, dict) and result.get("success", False)))
        
        return summary
    
    async def get_health_indicators(self) -> Dict[str, Any]:
        """
        Get health indicators for the architecture.
        
        Returns:
            Dictionary with health indicators for different aspects
        """
        latest_results = await self.get_latest_diagnostic_results()
        current_metrics = get_metrics()
        
        health = {
            "overall": "unknown",
            "layers": {},
            "cross_layer_calls": "unknown",
            "property_tracking": "unknown"
        }
        
        # Check architecture validation
        arch_validation = latest_results.get("architecture_validation", {})
        if arch_validation:
            health["overall"] = "healthy" if arch_validation.get("success", False) else "unhealthy"
            
            # Check individual layers
            results = arch_validation.get("results", {})
            if results:
                health["layers"] = {
                    "storage_layer": "healthy" if results.get("storage_layer", False) else "unhealthy",
                    "processing_layer": "healthy" if results.get("processing_layer", False) else "unhealthy",
                    "api_layer": "healthy" if results.get("api_layer", False) else "unhealthy"
                }
        
        # Check property tracking
        tracking = latest_results.get("property_tracking", {})
        if tracking:
            tracking_results = tracking.get("results", {})
            health["property_tracking"] = "healthy" if tracking.get("success", False) else "unhealthy"
        
        # Check cross-layer calls
        if current_metrics and "cross_layer_calls" in current_metrics:
            if current_metrics["cross_layer_calls"]:
                error_rate = sum(current_metrics.get("cross_layer_errors", {}).values()) / sum(current_metrics["cross_layer_calls"].values()) if sum(current_metrics["cross_layer_calls"].values()) > 0 else 0
                
                if error_rate < 0.01:  # Less than 1% error rate
                    health["cross_layer_calls"] = "healthy"
                elif error_rate < 0.05:  # Less than 5% error rate
                    health["cross_layer_calls"] = "warning"
                else:
                    health["cross_layer_calls"] = "unhealthy"
        
        return health