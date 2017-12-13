# -*- coding: utf-8 -*-
# © 2017 Akretion, Mourad EL HADJ MIMOUNE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr
    # Update exception_rule for sale.order and sale.order.line:
    cr.execute(
        '''UPDATE exception_rule
        SET rule_group = 'sale'
        WHERE model ='sale.order' or model = 'sale.order.line'
        ''')
    cr.execute(
        '''UPDATE ir_model_data
        SET model = 'exception.rule'
        WHERE model ='sale.exception'
        ''')
