"""
Django-like signals system for models.

Usage:
    from project.core.db.signals import pre_save, post_save
    
    @pre_save.connect
    def my_pre_save_handler(sender, instance, **kwargs):
        print(f"About to save {instance}")
    
    @post_save.connect
    def my_post_save_handler(sender, instance, created, **kwargs):
        if created:
            print(f"Created {instance}")
        else:
            print(f"Updated {instance}")
"""

from __future__ import annotations

import weakref
import inspect
import logging
from typing import Any, Callable, Optional, ParamSpec, Type

P = ParamSpec("P")


class Signal:
    """Django-like signal dispatcher."""

    def __init__(self) -> None:
        self._receivers: list[tuple[Callable, Optional[weakref.ref]]] = []

    def connect(self, receiver: Callable[P, Any], sender: Optional[Type] = None, weak: bool = True) -> None:
        """
        Connect a receiver function to this signal.
        
        Args:
            receiver: The callback function
            sender: Optional model class to filter by sender
            weak: Use weak references (default: True)
        """
        if weak:
            receiver_ref = weakref.ref(receiver)
        else:
            receiver_ref = None

        self._receivers.append((receiver, receiver_ref, sender))

    def disconnect(self, receiver: Callable[P, Any], sender: Optional[Type] = None) -> None:
        """Disconnect a receiver from this signal."""
        to_remove = []
        for i, (recv, ref, send) in enumerate(self._receivers):
            if ref is not None:
                if ref() is receiver and send == sender:
                    to_remove.append(i)
            elif recv is receiver and send == sender:
                to_remove.append(i)

        for i in reversed(to_remove):
            del self._receivers[i]

    async def send(self, sender: Type, **kwargs: Any) -> list[tuple[Callable, Any]]:
        """
        Send signal to all connected receivers.
        
        Returns:
            List of (receiver, response) tuples
        """
        responses = []
        for receiver, ref, signal_sender in self._receivers:
            # Check if sender matches (if specified)
            if signal_sender is not None and not issubclass(sender, signal_sender):
                continue

            # Get receiver (handle weak refs)
            if ref is not None:
                receiver_func = ref()
                if receiver_func is None:
                    continue  # Weak ref was garbage collected
            else:
                receiver_func = receiver

            # Call receiver
            if receiver_func is not None:
                try:
                    # Check if it's async
                    if hasattr(receiver_func, "__call__"):
                        if inspect.iscoroutinefunction(receiver_func):
                            response = await receiver_func(sender=sender, **kwargs)
                        else:
                            response = receiver_func(sender=sender, **kwargs)
                        responses.append((receiver_func, response))
                except Exception as e:
                    # Log error but don't stop other receivers
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error in signal receiver {receiver_func}: {e}", exc_info=True)

        return responses

    def send_sync(self, sender: Type, **kwargs: Any) -> list[tuple[Callable, Any]]:
        """
        Send signal synchronously (for sync receivers only).
        
        Returns:
            List of (receiver, response) tuples
        """
        responses = []
        for receiver, ref, signal_sender in self._receivers:
            if signal_sender is not None and not issubclass(sender, signal_sender):
                continue

            if ref is not None:
                receiver_func = ref()
                if receiver_func is None:
                    continue
            else:
                receiver_func = receiver

            if receiver_func is not None:
                try:
                    response = receiver_func(sender=sender, **kwargs)
                    responses.append((receiver_func, response))
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error in signal receiver {receiver_func}: {e}", exc_info=True)

        return responses


# Django-like signal instances
pre_save = Signal()
post_save = Signal()
pre_delete = Signal()
post_delete = Signal()
pre_init = Signal()
post_init = Signal()
m2m_changed = Signal()  # For many-to-many changes

__all__ = [
    "Signal",
    "pre_save",
    "post_save",
    "pre_delete",
    "post_delete",
    "pre_init",
    "post_init",
    "m2m_changed",
]

