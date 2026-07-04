"""Webhook handler for receiving events from JAWIS."""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from fastapi import HTTPException

from ..events.dispatcher import get_dispatcher
from ..events.event_types import create_event_from_type
from .schemas import WebhookEventSchema, WebhookResponseSchema

logger = logging.getLogger(__name__)


class JawisWebhookHandler:
    """
    Handler for processing webhook events from JAWIS.
    
    Receives business events from JAWIS and converts them to internal events
    for processing by the event system.
    """
    
    def __init__(self):
        """Initialize the webhook handler."""
        self.dispatcher = get_dispatcher()
        self.processed_events = 0
        self.failed_events = 0
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> WebhookResponseSchema:
        """
        Process a webhook event from JAWIS.
        
        Args:
            webhook_data: Raw webhook data from JAWIS
            
        Returns:
            WebhookResponseSchema with processing result
        """
        try:
            # Validate webhook data
            webhook_event = WebhookEventSchema(**webhook_data)
            
            logger.info(f"Received webhook event: {webhook_event.event_type} ({webhook_event.event_id})")
            
            # Create internal event from webhook data
            internal_event = create_event_from_type(
                event_type=webhook_event.event_type,
                event_id=webhook_event.event_id,
                timestamp=webhook_event.timestamp,
                source=webhook_event.source,
                data=webhook_event.data,
                metadata=webhook_event.metadata
            )
            
            # Dispatch event to handlers
            results = await self.dispatcher.dispatch(internal_event)
            
            # Check if any handler processed successfully
            successful_results = [r for r in results if r.success]
            failed_results = [r for r in results if not r.success]
            
            if successful_results:
                self.processed_events += 1
                logger.info(f"Webhook event {webhook_event.event_id} processed successfully by {len(successful_results)} handlers")
                
                return WebhookResponseSchema(
                    success=True,
                    event_id=webhook_event.event_id,
                    message=f"Event processed by {len(successful_results)} handlers"
                )
            else:
                self.failed_events += 1
                error_messages = [r.error for r in failed_results if r.error]
                logger.error(f"Webhook event {webhook_event.event_id} failed processing: {error_messages}")
                
                return WebhookResponseSchema(
                    success=False,
                    event_id=webhook_event.event_id,
                    message="Event processing failed",
                    errors=error_messages
                )
                
        except ValueError as e:
            # Event type not supported
            logger.warning(f"Unsupported event type in webhook: {str(e)}")
            return WebhookResponseSchema(
                success=False,
                event_id=webhook_data.get("event_id", "unknown"),
                message="Unsupported event type",
                errors=[str(e)]
            )
            
        except Exception as e:
            # Unexpected error
            logger.error(f"Webhook processing error: {str(e)}")
            self.failed_events += 1
            
            return WebhookResponseSchema(
                success=False,
                event_id=webhook_data.get("event_id", "unknown"),
                message="Internal processing error",
                errors=[str(e)]
            )
    
    async def handle_batch_webhook(self, webhook_events: List[Dict[str, Any]]) -> List[WebhookResponseSchema]:
        """
        Process multiple webhook events in batch.
        
        Args:
            webhook_events: List of webhook event data
            
        Returns:
            List of WebhookResponseSchema for each event
        """
        results = []
        
        for webhook_data in webhook_events:
            try:
                result = await self.handle_webhook(webhook_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch webhook processing error: {str(e)}")
                results.append(WebhookResponseSchema(
                    success=False,
                    event_id=webhook_data.get("event_id", "unknown"),
                    message="Batch processing error",
                    errors=[str(e)]
                ))
        
        return results
    
    def validate_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """
        Validate webhook signature for security.
        
        Args:
            payload: Raw webhook payload bytes
            signature: Webhook signature from headers
            secret: Webhook secret for validation
            
        Returns:
            bool: True if signature is valid
        """
        # TODO: Implement webhook signature validation
        # This would typically use HMAC-SHA256 with the webhook secret
        logger.warning("Webhook signature validation not implemented")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get webhook processing statistics."""
        return {
            "processed_events": self.processed_events,
            "failed_events": self.failed_events,
            "success_rate": (
                self.processed_events / (self.processed_events + self.failed_events)
                if (self.processed_events + self.failed_events) > 0
                else 0
            ),
            "dispatcher_metrics": self.dispatcher.get_metrics()
        }
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.processed_events = 0
        self.failed_events = 0


# Global webhook handler instance
_global_webhook_handler: Optional[JawisWebhookHandler] = None


def get_webhook_handler() -> JawisWebhookHandler:
    """Get the global webhook handler instance."""
    global _global_webhook_handler
    if _global_webhook_handler is None:
        _global_webhook_handler = JawisWebhookHandler()
    return _global_webhook_handler
