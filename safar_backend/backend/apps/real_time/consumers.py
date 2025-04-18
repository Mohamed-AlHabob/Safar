import json
import logging
from uuid import UUID
from typing import Dict, List, Any
from django.core.cache import cache
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q
from apps.safar.models import Booking, Message, Notification
from apps.safar.serializers import (
    BookingSerializer,
    MessageSerializer,
    NotificationSerializer
)

logger = logging.getLogger(__name__)

class UUIDEncoder(json.JSONEncoder):
    """JSON encoder that handles UUIDs and other complex types"""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if hasattr(obj, '__dict__'):
            return vars(obj)
        return super().default(obj)

class SafariConsumer(AsyncJsonWebsocketConsumer):
    """Enhanced WebSocket consumer with robust connection handling"""
    
    # Group prefixes for different notification types
    BOOKING_GROUP = 'bookings_'
    MESSAGE_GROUP = 'messages_'
    NOTIFICATION_GROUP = 'notifications_'
    GENERAL_GROUP = 'safar_'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.groups = []
        self._connected = False
        self.cache_timeout = 300  # 5 minutes

    async def connect(self):
        """Handle WebSocket connection with improved reliability"""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            logger.warning("Rejected anonymous WebSocket connection")
            await self.close(code=4001)
            return

        try:
            # Accept connection first to establish the WebSocket
            await self.accept()
            self._connected = True
            
            # Add user to all relevant groups
            self.groups = [
                f"{self.BOOKING_GROUP}{self.user.id}",
                f"{self.MESSAGE_GROUP}{self.user.id}",
                f"{self.NOTIFICATION_GROUP}{self.user.id}",
                f"{self.GENERAL_GROUP}{self.user.id}"
            ]
            
            for group in self.groups:
                await self.channel_layer.group_add(group, self.channel_name)
            
            logger.info(f"WebSocket connection established for user {self.user.id}")
            
            # Send initial data with comprehensive error handling
            await self._send_initial_data()
            
        except Exception as e:
            logger.error(f"Error during WebSocket setup: {str(e)}", exc_info=True)
            self._connected = False
            await self.close(code=1011)  # Internal error

    async def _send_initial_data(self):
        """Handle sending initial data with connection checks"""
        if not self._connected:
            return
            
        try:
            initial_data = await self._get_cached_initial_data()
            response = {
                "type": "initial_data",
                "payload": initial_data
            }
            await self.send_json(response)
        except Exception as e:
            logger.error(f"Error sending initial data: {str(e)}", exc_info=True)
            await self._send_error(f"Failed to load initial data: {str(e)}")

    async def disconnect(self, close_code: int):
        """Clean up on WebSocket disconnect"""
        self._connected = False
        if self.user and not self.user.is_anonymous:
            try:
                # Remove from all groups
                for group in self.groups:
                    await self.channel_layer.group_discard(group, self.channel_name)
                
                logger.info(f"WebSocket connection closed for user {self.user.id} with code {close_code}")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")

    async def _get_cached_initial_data(self) -> Dict:
        """Get initial data with Redis caching for performance"""
        cache_key = f"ws_initial_data_{self.user.id}"
        
        try:
            cached_data = await cache.aget(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            data = await self._fetch_initial_data()
            serialized_data = json.dumps(data, cls=UUIDEncoder)
            await cache.aset(cache_key, serialized_data, timeout=self.cache_timeout)
            return data
            
        except Exception as e:
            logger.error(f"Cache error: {str(e)}")
            return await self._fetch_initial_data()

    async def _fetch_initial_data(self) -> Dict:
        """Fetch all initial data with optimized queries"""
        try:
            bookings, messages, notifications = await database_sync_to_async(
                self._get_initial_data_sync
            )()
            
            return {
                "bookings": bookings,
                "messages": messages,
                "notifications": notifications
            }
        except Exception as e:
            logger.error(f"Error fetching initial data: {str(e)}", exc_info=True)
            raise

    def _get_initial_data_sync(self) -> tuple:
        """Synchronous method to fetch all initial data"""
        bookings = BookingSerializer(
            Booking.objects.filter(user=self.user)
            .select_related('place', 'experience', 'flight', 'box')
            .order_by('-booking_date')[:10],
            many=True
        ).data
        
        messages = MessageSerializer(
            Message.objects.filter(
                Q(sender=self.user) | Q(receiver=self.user)
            )
            .select_related('sender', 'receiver')
            .order_by('-created_at')[:20],
            many=True
        ).data
        
        notifications = NotificationSerializer(
            Notification.objects.filter(
                user=self.user,
                is_read=False
            )
            .order_by('-created_at')[:50],
            many=True
        ).data
        
        return bookings, messages, notifications

    async def receive_json(self, content: Dict, **kwargs):
        """Handle incoming WebSocket messages"""
        if not self._connected:
            return
            
        try:
            action = content.get("action")
            payload = content.get("payload", {})
            
            if not action:
                await self._send_error("Missing 'action' field")
                return
                
            handlers = {
                "mark_message_read": self._handle_mark_message_read,
                "mark_notification_read": self._handle_mark_notification_read,
                "mark_all_notifications_read": self._handle_mark_all_notifications_read,
                "get_more_messages": self._handle_get_more_messages,
                "ping": self._handle_ping
            }
            
            handler = handlers.get(action)
            if handler:
                await handler(payload)
            else:
                await self._send_error(f"Unknown action: {action}")
                
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}", exc_info=True)
            await self._send_error(f"Server error: {str(e)}")

    async def _handle_ping(self, payload: Dict):
        """Handle ping messages to keep connection alive"""
        if not self._connected:
            return
            
        response = {
            "type": "pong",
            "payload": {
                "timestamp": self._get_timestamp()
            }
        }
        await self.send_json(response)

    def _get_timestamp(self):
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def _handle_mark_message_read(self, payload: Dict):
        """Mark a message as read"""
        message_id = payload.get("message_id")
        if not message_id:
            await self._send_error("Message ID is required")
            return
            
        try:
            success = await database_sync_to_async(self._mark_message_read_sync)(message_id)
            if success:
                await self._invalidate_cache()
                response = {
                    "type": "message_marked_read",
                    "payload": {"message_id": message_id}
                }
                await self.send_json(response)
            else:
                await self._send_error("Message not found or not authorized")
        except Exception as e:
            logger.error(f"Error marking message read: {str(e)}")
            await self._send_error(f"Failed to mark message as read: {str(e)}")

    def _mark_message_read_sync(self, message_id) -> bool:
        """Sync version of mark message read"""
        try:
            return Message.objects.filter(
                id=message_id, 
                receiver=self.user,
                is_read=False
            ).update(is_read=True) > 0
        except Exception as e:
            logger.error(f"Database error marking message read: {str(e)}")
            return False

    async def _handle_mark_notification_read(self, payload: Dict):
        """Mark a notification as read"""
        notification_id = payload.get("notification_id")
        if not notification_id:
            await self._send_error("Notification ID is required")
            return
            
        try:
            success = await database_sync_to_async(self._mark_notification_read_sync)(notification_id)
            if success:
                await self._invalidate_cache()
                response = {
                    "type": "notification_marked_read",
                    "payload": {"notification_id": notification_id}
                }
                await self.send_json(response)
            else:
                await self._send_error("Notification not found or not authorized")
        except Exception as e:
            logger.error(f"Error marking notification read: {str(e)}")
            await self._send_error(f"Failed to mark notification as read: {str(e)}")

    def _mark_notification_read_sync(self, notification_id) -> bool:
        """Sync version of mark notification read"""
        try:
            return Notification.objects.filter(
                id=notification_id,
                user=self.user,
                is_read=False
            ).update(is_read=True) > 0
        except Exception as e:
            logger.error(f"Database error marking notification read: {str(e)}")
            return False

    async def _handle_mark_all_notifications_read(self, payload: Dict):
        """Mark all notifications as read"""
        try:
            count = await database_sync_to_async(self._mark_all_notifications_read_sync)()
            await self._invalidate_cache()
            response = {
                "type": "all_notifications_marked_read",
                "payload": {"count": count}
            }
            await self.send_json(response)
        except Exception as e:
            logger.error(f"Error marking all notifications read: {str(e)}")
            await self._send_error(f"Failed to mark all notifications as read: {str(e)}")

    def _mark_all_notifications_read_sync(self) -> int:
        """Mark all user's notifications as read"""
        try:
            return Notification.objects.filter(
                user=self.user,
                is_read=False
            ).update(is_read=True)
        except Exception as e:
            logger.error(f"Database error marking all notifications read: {str(e)}")
            return 0

    async def _handle_get_more_messages(self, payload: Dict):
        """Handle request for more messages with pagination"""
        try:
            offset = int(payload.get("offset", 0))
            limit = min(int(payload.get("limit", 20)), 50)
            
            messages = await database_sync_to_async(self._get_more_messages_sync)(offset, limit)
            
            response = {
                "type": "more_messages",
                "payload": {
                    "messages": messages,
                    "offset": offset,
                    "limit": limit
                }
            }
            await self.send_json(response)
            
        except ValueError:
            await self._send_error("Invalid pagination parameters")
        except Exception as e:
            logger.error(f"Error fetching more messages: {str(e)}")
            await self._send_error(f"Failed to fetch more messages: {str(e)}")

    def _get_more_messages_sync(self, offset: int, limit: int) -> List:
        """Get paginated messages"""
        messages = Message.objects.filter(
            Q(sender=self.user) | Q(receiver=self.user)
        ).select_related(
            'sender', 'receiver'
        ).order_by(
            '-created_at'
        )[offset:offset+limit]
        
        return MessageSerializer(messages, many=True).data

    async def _invalidate_cache(self):
        """Invalidate cached initial data"""
        try:
            cache_key = f"ws_initial_data_{self.user.id}"
            await cache.adelete(cache_key)
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")

    async def _send_error(self, message: str):
        """Send error message to client with connection check"""
        if not self._connected:
            return
            
        try:
            error_message = {
                "type": "error",
                "payload": {"message": message}
            }
            await self.send_json(error_message)
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")

    # Event handlers for different message types
    async def booking_update(self, event: Dict):
        """Handle booking update events"""
        if self._connected:
            try:
                await self.send_json({
                    "type": "booking_update",
                    "payload": event.get("data", {})
                })
            except Exception as e:
                logger.error(f"Error sending booking update: {str(e)}")

    async def message_new(self, event: Dict):
        """Handle new message events"""
        if self._connected:
            try:
                await self.send_json({
                    "type": "new_message",
                    "payload": event.get("data", {})
                })
            except Exception as e:
                logger.error(f"Error sending new message: {str(e)}")

    async def notification_new(self, event: Dict):
        """Handle new notification events"""
        if self._connected:
            try:
                await self.send_json({
                    "type": "new_notification",
                    "payload": event.get("data", {})
                })
            except Exception as e:
                logger.error(f"Error sending new notification: {str(e)}")

    async def send_json(self, content, **kwargs):
        """Override send_json to include connection check"""
        if not self._connected:
            return
        try:
            await super().send_json(content, **kwargs)
        except Exception as e:
            logger.error(f"Error sending JSON data: {str(e)}")
            self._connected = False