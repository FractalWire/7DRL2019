from __future__ import annotations
from typing import Dict, List, Any
import logging
from common.logging import StyleAdapter
import common.topics as topics


logger = StyleAdapter(logging.getLogger(__name__))


class LogEntry:
    '''OBSOLETE'''

    def __init__(self, short: str, title: str = "", text: str = "") -> None:
        self.short = short
        self.title = title
        self.text = text

    @property
    def description(self) -> Dict[str, str]:
        return dict(title=self.title, text=self.text)


class Log:
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []
        topics.log.subscribe(self._ev_writelog)

    def _ev_writelog(self, args: Dict[str, Any] = {}) -> None:
        logger.debug("new log entry:", args)
        self.entries.append(args)
