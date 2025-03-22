from abc import ABC, abstractmethod


class INotificationService(ABC):
    @abstractmethod
    async def handle_event(self, data: dict) -> None: ...
