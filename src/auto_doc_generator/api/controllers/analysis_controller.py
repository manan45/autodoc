"""
Analysis API controller.

This module provides HTTP endpoints for code analysis functionality.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from ...core.services.analysis_service import AnalysisService
from ...core.exceptions.analysis_exceptions import AnalysisError

logger = logging.getLogger(__name__)


class AnalysisController:
    """Controller for analysis-related API endpoints."""
    
    def __init__(self, analysis_service: AnalysisService):
        """
        Initialize the analysis controller.
        
        Args:
            analysis_service: Service for performing analysis
        """
        self.analysis_service = analysis_service
        self.blueprint = Blueprint('analysis', __name__, url_prefix='/api/analysis')
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        self.blueprint.add_url_rule('', methods=['POST'], view_func=self.analyze_codebase)
        self.blueprint.add_url_rule('/file', methods=['POST'], view_func=self.analyze_file)
        self.blueprint.add_url_rule('/summary', methods=['POST'], view_func=self.get_summary)
        self.blueprint.add_url_rule('/status', methods=['GET'], view_func=self.get_status)
    
    def analyze_codebase(self):
        """
        Analyze an entire codebase.
        
        Expected JSON payload:
        {
            "repository_path": "/path/to/repo",
            "config": {...}  // optional
        }
        """
        try:
            data = request.get_json()
            
            if not data or 'repository_path' not in data:
                return jsonify({
                    'error': 'Missing required field: repository_path'
                }), 400
            
            repository_path = data['repository_path']
            config = data.get('config', {})
            
            # Update service config if provided
            if config:
                self.analysis_service.config.update(config)
            
            # Perform analysis
            result = self.analysis_service.analyze_codebase(repository_path)
            
            return jsonify({
                'success': True,
                'data': result.to_dict()
            })
            
        except AnalysisError as e:
            logger.error(f"Analysis error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 422
            
        except Exception as e:
            logger.exception(f"Unexpected error in analyze_codebase: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    def analyze_file(self):
        """
        Analyze a single file.
        
        Expected JSON payload:
        {
            "file_path": "/path/to/file.py"
        }
        """
        try:
            data = request.get_json()
            
            if not data or 'file_path' not in data:
                return jsonify({
                    'error': 'Missing required field: file_path'
                }), 400
            
            file_path = data['file_path']
            
            # Perform single file analysis
            result = self.analysis_service.analyze_single_file(file_path)
            
            if result is None:
                return jsonify({
                    'success': False,
                    'error': 'Failed to analyze file'
                }), 422
            
            return jsonify({
                'success': True,
                'data': result.__dict__
            })
            
        except AnalysisError as e:
            logger.error(f"Analysis error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 422
            
        except Exception as e:
            logger.exception(f"Unexpected error in analyze_file: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    def get_summary(self):
        """
        Get analysis summary.
        
        Expected JSON payload:
        {
            "analysis_result": {...}  // AnalysisResult dict
        }
        """
        try:
            data = request.get_json()
            
            if not data or 'analysis_result' not in data:
                return jsonify({
                    'error': 'Missing required field: analysis_result'
                }), 400
            
            # This would need proper deserialization in a real implementation
            # For now, assume the data is already in the right format
            analysis_data = data['analysis_result']
            
            # Create a mock AnalysisResult for the summary
            # In practice, you'd want to properly deserialize this
            summary = {
                'repository_path': analysis_data.get('repository_path', ''),
                'total_files': len(analysis_data.get('modules', [])),
                'total_functions': sum(len(m.get('functions', [])) for m in analysis_data.get('modules', [])),
                'total_classes': sum(len(m.get('classes', [])) for m in analysis_data.get('modules', [])),
                'languages_detected': analysis_data.get('languages_detected', []),
                'project_type': analysis_data.get('project_type', 'unknown'),
            }
            
            return jsonify({
                'success': True,
                'data': summary
            })
            
        except Exception as e:
            logger.exception(f"Unexpected error in get_summary: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    def get_status(self):
        """Get analysis service status."""
        try:
            status = {
                'service': 'analysis',
                'status': 'healthy',
                'version': '2.0.0',
                'capabilities': [
                    'codebase_analysis',
                    'single_file_analysis', 
                    'ast_parsing',
                    'complexity_metrics',
                    'dependency_analysis'
                ]
            }
            
            return jsonify({
                'success': True,
                'data': status
            })
            
        except Exception as e:
            logger.exception(f"Unexpected error in get_status: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
