from __future__ import annotations
from typing import Dict, Any
import logging
from common.logging import StyleAdapter
from pubsub import pub

logger = StyleAdapter(logging.getLogger(__name__))

logger.info('topics initiatlization')

PLAYER_LOG_NAME = 'log'
DESCRIPTION_NAME = 'description.value'
DEFAULT_DESCRIPTION_NAME = 'description.default'
TEXT_DESCRIPTION_NAME = 'description.text'

topic_manager = pub.getDefaultTopicMgr()


logger.debug('topics creation started')


def _prot_args(args: Dict[str, Any] = None) -> None: pass


def _prot_value(value: Any) -> None: pass


log = topic_manager.getOrCreateTopic(PLAYER_LOG_NAME, _prot_args)

description = topic_manager.getOrCreateTopic(DESCRIPTION_NAME, _prot_args)
default_description = topic_manager.getOrCreateTopic(
    DEFAULT_DESCRIPTION_NAME, _prot_args)
text_description = topic_manager.getOrCreateTopic(
    TEXT_DESCRIPTION_NAME, _prot_value)

logger.debug('topics creation done')
