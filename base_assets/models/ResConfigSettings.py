# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from odoo.osv import expression


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    trans_department = fields.Many2one("hr.department", "Trans Department",
                                       config_parameter='base_assets.trans_department', )
    max_trans_day = fields.Integer("Max Trans", help="Max Days with assets applied in trans",
                                   config_parameter='base_assets.max_trans_day',)
