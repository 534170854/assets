# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from six import integer_types


class ResUsers(models.Model):
    _inherit = 'res.users'

    employee_id = fields.Many2one("hr.employee", "Employee", compute="_get_employee", inverse="_set_employee", index=True)
    department_id = fields.Many2one("hr.department", "Department", compute="_get_employee", inverse="_set_employee", index=True)
    department_ids = fields.Many2many("hr.department", "urse_department_rel", "user_id", "department_id", "Department",
                                      compute="_get_employee", inverse="_set_employee")

    @api.multi
    @api.depends("employee_ids")
    def _get_employee(self):
        hr_department_env = self.env["hr.department"]
        for user in self:
            if user.employee_ids:
                user.employee_id = user.employee_ids[0].id
                user.department_id = user.employee_ids[0].department_id.id
                user.department_ids = hr_department_env.search(
                    [("id", "child_of", user.employee_ids[0].department_id.id)]).ids
            else:
                user.employee_id = False
                user.department_id = False
                user.department_ids = False

    @api.one
    def _set_employee(self):
        pass


    # 触发重新计算用户的员工、部门、所有下级部门
    def compute_user_id(self):
        self._get_employee()

    def compute_user_id_all(self, user_id=None):
        if user_id and isinstance(user_id, integer_types):
            user_id = self.browse(integer_types)
        elif user_id:
            pass
        else:
            user_id = self.search([])
        user_id._get_employee()