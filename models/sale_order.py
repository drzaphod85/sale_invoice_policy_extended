# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    invoice_policy = fields.Selection(
        [("order", "Ordered quantities"), ("delivery", "Delivered quantities")],
        help="Ordered Quantity: Invoice based on the quantity the customer "
        "ordered.\n"
        "Delivered Quantity: Invoiced based on the quantity the vendor "
        "delivered (time or deliveries).",
    )
    invoice_policy_required = fields.Boolean(
        compute="_compute_invoice_policy_required",
        default=lambda self: self.env["ir.default"]._get(
            "res.config.settings", "sale_invoice_policy_required"
        ),
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        default_invoice_policy = (
            self.env["res.config.settings"]
            .sudo()
            .default_get(["default_invoice_policy"])
            .get("default_invoice_policy", False)
        )
        if "invoice_policy" not in res:
            res.update({"invoice_policy": default_invoice_policy})
        return res

    @api.depends("partner_id")
    def _compute_invoice_policy_required(self):
        invoice_policy_required = (
            self.env["res.config.settings"]
            .sudo()
            .default_get(["sale_invoice_policy_required"])
            .get("sale_invoice_policy_required", False)
        )
        for sale in self:
            sale.invoice_policy_required = invoice_policy_required

    @api.onchange("partner_id")
    def _onchange_partner_invoice_policy(self):
        if self.partner_id and self.partner_id.default_invoice_policy:
            self.invoice_policy = self.partner_id.default_invoice_policy

    @api.model_create_multi
    def create(self, vals_list):
        """Apply the partner's default invoice policy at create time.

        The existing ``_onchange_partner_invoice_policy`` only fires in
        the web client. This override applies the same fallback when a
        sale order is created from any other context — eCommerce
        checkout (``website_sale``), API calls, scripts, imports, or
        unit tests — so the per-partner default is honored everywhere,
        not just in the backend form view.

        Precedence (highest to lowest):
            1. Explicit ``invoice_policy`` in ``vals``  (caller wins)
            2. ``partner_id.default_invoice_policy`` if set
            3. The system default applied by ``default_get`` (untouched)
        """
        for vals in vals_list:
            if "invoice_policy" in vals or not vals.get("partner_id"):
                continue
            partner = self.env["res.partner"].browse(vals["partner_id"])
            if partner.default_invoice_policy:
                vals["invoice_policy"] = partner.default_invoice_policy
        return super().create(vals_list)

    def write(self, vals):
        if "invoice_policy" in vals:
            _logger.debug(
                "Updating invoice policy for orders %s to %s",
                self.mapped("name"),
                vals["invoice_policy"],
            )
        return super().write(vals)
