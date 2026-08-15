"""
Verification Adapter for Agent API
Connects the CompleteAIAgent to the verification layer with real response validation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from knowledge_layer.verification.verification_layer import VerificationLayer, VerificationResult, VerificationStatus
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class VerificationAdapter:
    """Adapter for verification layer with real response validation"""
    
    def __init__(self):
        self.verification_layer = VerificationLayer()
    
    def verify_response(self, response: str, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Verify an AI response"""
        try:
            # Run all verification checks
            results = self.verification_layer.verify_response(response, query)
            
            # Get overall status
            status, score = self.verification_layer.get_overall_status(results)
            
            # Convert results to serializable format
            serializable_results = {}
            for check_name, result in results.items():
                serializable_results[check_name] = {
                    'status': result.status.value,
                    'score': result.score,
                    'message': result.message,
                    'details': result.details
                }
            
            return {
                'overall_status': status.value,
                'overall_score': score,
                'checks': serializable_results,
                'passed': status == VerificationStatus.PASSED,
                'needs_review': status in [VerificationStatus.WARNING, VerificationStatus.REVIEW_NEEDED],
                'failed': status == VerificationStatus.FAILED
            }
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {
                'overall_status': 'error',
                'overall_score': 0.0,
                'checks': {},
                'passed': False,
                'needs_review': True,
                'failed': True,
                'error': str(e)
            }
    
    def get_verification_summary(self, verification_result: Dict[str, Any]) -> str:
        """Get a human-readable summary of verification results"""
        if verification_result.get('error'):
            return f"Verification error: {verification_result['error']}"
        
        status = verification_result['overall_status']
        score = verification_result['overall_score']
        
        summary = f"Verification {status} (score: {score:.2f})\n"
        
        failed_checks = [
            check_name for check_name, result in verification_result['checks'].items()
            if result['status'] == 'failed'
        ]
        
        if failed_checks:
            summary += f"Failed checks: {', '.join(failed_checks)}\n"
        
        warning_checks = [
            check_name for check_name, result in verification_result['checks'].items()
            if result['status'] == 'warning'
        ]
        
        if warning_checks:
            summary += f"Warnings: {', '.join(warning_checks)}\n"
        
        return summary
