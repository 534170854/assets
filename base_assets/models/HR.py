# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Employee(models.Model):
    _inherit = ['hr.employee']

    _sql_constraints = [('user_id_unique', 'unique(user_id)', 'A user can only have one Employee.')]


class Department(models.Model):
    _inherit = ['hr.department']

    active = fields.Boolean("Active", default=True, index=True)
