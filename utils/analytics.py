"""
Advanced analytics and reporting for PPE detection compliance.
Generates metrics, trends, and insights from detection logs.
PHASE 4: Real database integration and advanced analytics.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

from Auth.db import SessionLocal, DetectionLog, Workstation, Organization
from utils.compliance import ComplianceStatus

logger = logging.getLogger(__name__)


class ComplianceAnalytics:
    """
    Generate analytics and insights from detection logs.
    """
    
    @staticmethod
    def get_organization_stats(
        org_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """
        Get comprehensive organization statistics.
        
        Args:
            org_id: Organization ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with aggregated statistics
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        db = SessionLocal()
        try:
            # Get all workstations for organization
            workstations = db.query(Workstation).filter(
                Workstation.org_id == org_id
            ).all()
            
            ws_ids = [ws.id for ws in workstations]
            
            if not ws_ids:
                return {
                    "total_detections": 0,
                    "total_workers": 0,
                    "compliant": 0,
                    "partial": 0,
                    "non_compliant": 0,
                    "compliance_rate": 0.0,
                    "workstations": 0,
                }
            
            # Query detection logs
            logs = db.query(DetectionLog).filter(
                DetectionLog.workstation_id.in_(ws_ids),
                DetectionLog.frame_timestamp >= start_date,
                DetectionLog.frame_timestamp <= end_date
            ).all()
            
            if not logs:
                return {
                    "total_detections": 0,
                    "total_workers": 0,
                    "compliant": 0,
                    "partial": 0,
                    "non_compliant": 0,
                    "compliance_rate": 0.0,
                    "workstations": len(ws_ids),
                }
            
            # Aggregate statistics
            total_detections = len(logs)
            total_workers = sum(log.worker_count or 0 for log in logs)
            total_compliant = sum(log.compliant_count or 0 for log in logs)
            total_partial = sum(log.partial_count or 0 for log in logs)
            total_non_compliant = sum(log.non_compliant_count or 0 for log in logs)
            
            compliance_rate = (
                (total_compliant / total_workers * 100)
                if total_workers > 0 else 0.0
            )
            
            return {
                "total_detections": total_detections,
                "total_workers": total_workers,
                "compliant": total_compliant,
                "partial": total_partial,
                "non_compliant": total_non_compliant,
                "compliance_rate": compliance_rate,
                "workstations": len(ws_ids),
                "start_date": start_date,
                "end_date": end_date,
            }
        
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return {}
        
        finally:
            db.close()
    
    @staticmethod
    def get_daily_trends(
        org_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Get daily compliance trends.
        
        Args:
            org_id: Organization ID
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with daily statistics
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        db = SessionLocal()
        try:
            workstations = db.query(Workstation).filter(
                Workstation.org_id == org_id
            ).all()
            
            ws_ids = [ws.id for ws in workstations]
            
            if not ws_ids:
                return pd.DataFrame()
            
            logs = db.query(DetectionLog).filter(
                DetectionLog.workstation_id.in_(ws_ids),
                DetectionLog.frame_timestamp >= start_date,
                DetectionLog.frame_timestamp <= end_date
            ).all()
            
            if not logs:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for log in logs:
                data.append({
                    "date": log.frame_timestamp.date(),
                    "timestamp": log.frame_timestamp,
                    "worker_count": log.worker_count or 0,
                    "compliant": log.compliant_count or 0,
                    "partial": log.partial_count or 0,
                    "non_compliant": log.non_compliant_count or 0,
                    "compliance_rate": (
                        (log.compliant_count / log.worker_count * 100)
                        if log.worker_count else 0
                    ),
                })
            
            df = pd.DataFrame(data)
            
            # Aggregate by date
            daily = df.groupby("date").agg({
                "worker_count": "sum",
                "compliant": "sum",
                "partial": "sum",
                "non_compliant": "sum",
                "compliance_rate": "mean",
            }).reset_index()
            
            daily["date"] = pd.to_datetime(daily["date"])
            
            return daily
        
        except Exception as e:
            logger.error(f"Trends error: {str(e)}")
            return pd.DataFrame()
        
        finally:
            db.close()
    
    @staticmethod
    def get_workstation_stats(
        workstation_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """
        Get statistics for specific workstation.
        
        Args:
            workstation_id: Workstation ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Workstation statistics
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        db = SessionLocal()
        try:
            logs = db.query(DetectionLog).filter(
                DetectionLog.workstation_id == workstation_id,
                DetectionLog.frame_timestamp >= start_date,
                DetectionLog.frame_timestamp <= end_date
            ).all()
            
            if not logs:
                return {"error": "No data available"}
            
            total_detections = len(logs)
            total_workers = sum(log.worker_count or 0 for log in logs)
            total_compliant = sum(log.compliant_count or 0 for log in logs)
            
            compliance_rate = (
                (total_compliant / total_workers * 100)
                if total_workers > 0 else 0.0
            )
            
            return {
                "workstation_id": workstation_id,
                "detections": total_detections,
                "total_workers": total_workers,
                "compliant": total_compliant,
                "compliance_rate": compliance_rate,
            }
        
        except Exception as e:
            logger.error(f"Workstation stats error: {str(e)}")
            return {}
        
        finally:
            db.close()
    
    @staticmethod
    def get_ppe_stats(
        org_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """
        Get PPE detection statistics.
        
        Args:
            org_id: Organization ID
            start_date: Start date
            end_date: End date
            
        Returns:
            PPE statistics
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        db = SessionLocal()
        try:
            workstations = db.query(Workstation).filter(
                Workstation.org_id == org_id
            ).all()
            
            ws_ids = [ws.id for ws in workstations]
            
            if not ws_ids:
                return {}
            
            logs = db.query(DetectionLog).filter(
                DetectionLog.workstation_id.in_(ws_ids),
                DetectionLog.frame_timestamp >= start_date,
                DetectionLog.frame_timestamp <= end_date
            ).all()
            
            if not logs:
                return {}
            
            # Aggregate PPE data
            ppe_stats = {}
            for log in logs:
                if log.ppe_breakdown:
                    for ppe_item, count in log.ppe_breakdown.items():
                        if ppe_item not in ppe_stats:
                            ppe_stats[ppe_item] = 0
                        ppe_stats[ppe_item] += count
            
            return ppe_stats
        
        except Exception as e:
            logger.error(f"PPE stats error: {str(e)}")
            return {}
        
        finally:
            db.close()
    
    @staticmethod
    def get_compliance_distribution(
        org_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """
        Get distribution of compliance statuses.
        
        Args:
            org_id: Organization ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Compliance distribution
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        db = SessionLocal()
        try:
            workstations = db.query(Workstation).filter(
                Workstation.org_id == org_id
            ).all()
            
            ws_ids = [ws.id for ws in workstations]
            
            if not ws_ids:
                return {
                    "compliant": 0,
                    "partial": 0,
                    "non_compliant": 0,
                }
            
            logs = db.query(DetectionLog).filter(
                DetectionLog.workstation_id.in_(ws_ids),
                DetectionLog.frame_timestamp >= start_date,
                DetectionLog.frame_timestamp <= end_date
            ).all()
            
            if not logs:
                return {
                    "compliant": 0,
                    "partial": 0,
                    "non_compliant": 0,
                }
            
            total_compliant = sum(log.compliant_count or 0 for log in logs)
            total_partial = sum(log.partial_count or 0 for log in logs)
            total_non_compliant = sum(log.non_compliant_count or 0 for log in logs)
            
            return {
                "compliant": total_compliant,
                "partial": total_partial,
                "non_compliant": total_non_compliant,
            }
        
        except Exception as e:
            logger.error(f"Distribution error: {str(e)}")
            return {}
        
        finally:
            db.close()