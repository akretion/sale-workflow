from openupgradelib import openupgrade

# flake8: noqa


def migrate(cr, version):
    # migrate sale.price.config from
    # sale_mrp_bom_configurable to sale_price_config
    openupgrade.update_module_moved_models(
        cr, "sale.price.config", "sale_mrp_bom_configurable", "sale_price_config"
    )
