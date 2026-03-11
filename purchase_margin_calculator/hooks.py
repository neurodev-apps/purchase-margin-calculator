# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def _post_init_populate_history(cr, registry):
    """Populate purchase price history from existing confirmed POs on install."""
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['product.template']._populate_history_from_existing()
