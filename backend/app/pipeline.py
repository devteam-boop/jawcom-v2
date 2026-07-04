"""Pipeline for processing events through the communication system."""

from typing import Dict, Any
from sqlalchemy.orm import Session
from .events.dispatcher import EventDispatcher
from .jawis.schemas import WebhookEventSchema
import logging

logger = logging.getLogger(__name__)


def process_jawis_event(event: WebhookEventSchema, db_session: Session) -> Dict[str, Any]:
    """
    Process JAWIS event through the complete communication pipeline.
    
    Args:
        event: Webhook event from JAWIS
        db_session: Database session
        
    Returns:
        Processing result
    """
    try:
        logger.info(f"Processing JAWIS event: {event.event_id}")
        
        # Create event dispatcher
        dispatcher = EventDispatcher(db_session)
        
        # Dispatch event
        result = dispatcher.dispatch(event)
        
        return result
    except Exception as e:
        logger.error(f"Error processing JAWIS event: {str(e)}")
        return {
            "success": False,
            "event_id": event.event_id if event else "unknown",
            "message": f"Error processing event: {str(e)}"
        }
