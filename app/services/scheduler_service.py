import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
from typing import Optional
import logging
from app.services.rss_collection_service import rss_collection_service

# Configure logging for the scheduler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for managing background scheduled tasks."""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
    
    async def start(self):
        """Start the background scheduler."""
        if self.is_running:
            logger.info("Scheduler is already running")
            return
        
        try:
            self.scheduler = AsyncIOScheduler()
            
            # Schedule RSS collection every 15 minutes
            self.scheduler.add_job(
                func=self._collect_rss_feeds,
                trigger=IntervalTrigger(minutes=15),
                id='rss_collection',
                name='RSS Feed Collection',
                replace_existing=True,
                max_instances=1  # Prevent overlapping runs
            )
            
            # Schedule cleanup every day at 2 AM
            self.scheduler.add_job(
                func=self._daily_cleanup,
                trigger=CronTrigger(hour=2, minute=0),
                id='daily_cleanup',
                name='Daily Cleanup',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Background scheduler started successfully")
            
            # Run initial RSS collection
            asyncio.create_task(self._collect_rss_feeds())
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the background scheduler."""
        if not self.is_running or not self.scheduler:
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Background scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    async def _collect_rss_feeds(self):
        """Background task to collect RSS feeds."""
        try:
            logger.info("Starting scheduled RSS feed collection...")
            start_time = datetime.now()
            
            stats = await rss_collection_service.collect_all_feeds()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"RSS collection completed in {duration:.2f}s: {stats['new_articles_stored']} new articles")
            
        except Exception as e:
            logger.error(f"Error in scheduled RSS collection: {e}")
            import traceback
            traceback.print_exc()
    
    async def _daily_cleanup(self):
        """Background task for daily cleanup operations."""
        try:
            logger.info("Starting daily cleanup...")
            
            # This would be expanded to include other cleanup tasks
            # For now, the RSS service handles its own cleanup
            
            logger.info("Daily cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in daily cleanup: {e}")
    
    def get_job_status(self) -> dict:
        """Get status of scheduled jobs."""
        if not self.scheduler:
            return {"status": "not_started", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running" if self.is_running else "stopped",
            "jobs": jobs
        }
    
    async def trigger_rss_collection(self) -> dict:
        """Manually trigger RSS collection."""
        try:
            logger.info("Manually triggering RSS collection...")
            stats = await rss_collection_service.collect_all_feeds()
            return {"status": "success", "stats": stats}
        except Exception as e:
            logger.error(f"Error in manual RSS collection: {e}")
            return {"status": "error", "error": str(e)}

# Create global instance
scheduler_service = SchedulerService() 