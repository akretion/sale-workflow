import logging

from odoo import SUPERUSER_ID
from odoo.api import Environment

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Compute discount columns")
    env = Environment(cr, SUPERUSER_ID, {})

    query = """
    update sale_order_line
    set
        price_subtotal_no_discount = price_subtotal
    where discount = 0.0
    """
    cr.execute(query)

    query = """
    update sale_order
    set
        price_subtotal_no_discount = amount_untaxed
    """
    cr.execute(query)

    query = """
    select distinct order_id from sale_order_line where discount > 0.0;
    """

    cr.execute(query)
    order_ids = cr.fetchall()

    so = env["sale.order"].search([("id", "in", order_ids)])
    count = len(so)
    if count == 0:
        _logger.info("No sale orders to update found.")
        return
    _logger.info("Scheduling without discount prices update of %d orders", count)

    batch_size = 250
    for part in range(1 + count // batch_size):
        start = part * batch_size
        end = min((part + 1) * batch_size, count)
        if end > start:
            so[start:end].mapped("order_line").with_delay(
                description="Without discount price update batch %d-%d / %d"
                % (start + 1, end, count)
            )._update_discount_display_fields()
