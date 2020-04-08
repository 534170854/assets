# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


status = [("draft", "Draft"), ("confirm", "Confirm"), ("done", "Done"), ("cancel", "Cancel")]


class AssetApplyOrder(models.Model):
    _name = 'asset.apply.order'
    _description = 'Assets Apply Order'

    name = fields.Char("Name", copy=False, readonly=True)
    apply_user_id = fields.Many2one("res.users", "Apply Users", default=lambda self: self._uid,
                                    readonly=True, states={'draft': [('readonly', False)]})
    apply_employee_id = fields.Many2one("hr.employee", "Apply Employee",
                                        readonly=True, states={'draft': [('readonly', False)]}, required=True)
    department_id = fields.Many2one("hr.department", "Department",
                                    readonly=True, states={'draft': [('readonly', False)]}, required=True)
    date = fields.Datetime("Date", default=fields.Datetime.now,
                           readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one("hr.employee", "Employee", readonly=True, states={'draft': [('readonly', False)]},
                                  required=True)
    state = fields.Selection(status, string="Status", readonly=True, default="draft")
    company_id = fields.Many2one("res.company", "Company", required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'asset.pick.order'),
                                 readonly=True, states={'draft': [('readonly', False)]})
    line_ids = fields.One2many("asset.apply.order.line", "order_id", String="Lines",
                               readonly=True, states={'draft': [('readonly', False)]})
    asset_picking_order_ids = fields.One2many('asset.picking.order', "apply_id", "Asset Picking Order", copy=False,
                                              readonly=True)
    note = fields.Char("Note", readonly=True, states={'draft': [('readonly', False)]})

    @api.onchange("apply_user_id")
    def onchange_apply_user_id(self):
        if self.apply_user_id.employee_id:
            self.apply_employee_id = self.apply_user_id.employee_id.id
            self.employee_id = self.apply_user_id.employee_id.id
        else:
            return {'warning':
                {
                    'title': _("Warning"),
                    'message': _("You must to binding an employee to your users to continue!"),
                },
                'value': {
                    "apply_employee_id": False,
                }
            }

    @api.onchange("employee_id")
    def onchange_employee_id(self):
        if self.employee_id.department_id:
            self.department_id = self.employee_id.department_id.id
        else:
            return {'warning':
                {
                    'title': _("Warning"),
                    'message': _("You must to choise an employee!"),
                },
                'value': {
                    "department_id": False,
                }
            }

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("asset.apply.order") or "New"
        return super(AssetApplyOrder, self).create(values)

    @api.multi
    def unlink(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(_("Only state of draft can be deleted"))
        res = super(AssetApplyOrder, self).unlink()
        return res

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_confirm(self):
        for order in self:
            if not order.line_ids:
                raise UserError(_("Must be have lines to do"))
        self.write({"state": "confirm"})

    def action_done(self):
        asset_picking_order_env = self.env["asset.picking.order"]
        for order in self:
            if order.asset_picking_order_ids:
                raise UserError(_("The order named %s has been done." % (order.name)))
            val = {
                "origin": order.name,
                "apply_id": order.id,
                "apply_user_id": order.apply_user_id.id,
                "apply_employee_id": order.apply_employee_id.id,
                "apply_department_id": order.department_id.id,
                "dest_owner_employee_id": order.employee_id.id,
                "dest_employee_id": order.employee_id.id,
                "dest_owner_department_id": order.department_id.id,
                "dest_department_id": order.employee_id.id,
                "date": order.date,
                "note": order.note,
            }
            line_ids = []
            for line in order.line_ids:
                quantity = line.quantity
                while quantity > 0:
                    line_ids.append((0, 0, {
                        "name": "%s Apply" % (line.product_id.display_name),
                        "product_id": line.product_id.id,
                        "date": order.date,
                        "dest_owner_employee_id": order.employee_id.id,
                        "dest_employee_id": order.employee_id.id,
                        "dest_owner_department_id": order.department_id.id,
                        "dest_department_id": order.employee_id.id,
                        "note": line.note,
                    }))
                    quantity = quantity - 1
            if line_ids:
                val["line_ids"] = line_ids
            else:
                raise UserError(_("Must be have lines to do"))
            asset_picking_order_env.create(val)
        self.write({"state": "done"})

    def action_view_pick(self):
        pick_ids = self.mapped("asset_picking_order_ids").ids
        action = self.env.ref("base_assets.asset_picking_order_action").read()[0]
        if len(pick_ids) == 1:
            action['res_id'] = pick_ids[0]
            action['views'] = [(False, 'form')]
        elif len(pick_ids) > 1:
            action['domain'] = [("id", "in", pick_ids)]
        else:
            raise UserError(_("The asset apply have not pick order!"))
        return action
    
class AssetPicOrderLine(models.Model):
    _name = 'asset.apply.order.line'

    order_id = fields.Many2one("asset.apply.order", "Order", index=True)
    name = fields.Char("Name")
    employee_id = fields.Many2one("hr.employee", "Employee", related="order_id.employee_id", store=True, index=True)
    department_id = fields.Many2one("hr.department", "Department", related="order_id.department_id", store=True, index=True)
    product_id = fields.Many2one("product.product", "Product", required=True, domain=[("is_asset", "=", True)], index=True)
    quantity = fields.Integer("Quantity")
    note = fields.Char("Note")
