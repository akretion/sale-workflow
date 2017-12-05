# -*- coding: utf-8 -*-
# © 2017 Akretion, Mourad EL HADJ MIMOUNE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr
    # Update move_name on account_bank_statement_line:
    cr.execute(
        '''UPDATE exception_rule
        SET rule_group = 'sale'
        WHERE model ='sale.order' or model = 'sale.order.line'
        ''')
