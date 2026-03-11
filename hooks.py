# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def _post_init_populate_history(env):
    """Populate purchase price history from existing confirmed POs on install."""
    env['product.template']._populate_history_from_existing()
