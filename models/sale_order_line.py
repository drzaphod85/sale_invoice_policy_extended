# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends(
        "qty_invoiced",
        "qty_delivered",
        "product_uom_qty",
        "state",
        "order_id.invoice_policy",
    )
    def _compute_qty_to_invoice(self):
        other_lines = self.filtered(
            lambda l: l.product_id.type == "service"
            or not l.order_id.invoice_policy
        )
        super(SaleOrderLine, other_lines)._compute_qty_to_invoice()
        for line in self - other_lines:
            invoice_policy = line.order_id.invoice_policy
            if invoice_policy == "order":
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = line.qty_delivered - line.qty_invoiced

    @api.depends(
        "state",
        "price_unit",
        "discount",
        "product_id",
        "untaxed_amount_invoiced",
        "qty_delivered",
        "product_uom_qty",
        "order_id.invoice_policy",
    )
    def _compute_untaxed_amount_to_invoice(self):
        other_lines = self.filtered(
            lambda line: line.product_id.type == "service"
            or not line.order_id.invoice_policy
            or line.order_id.invoice_policy == line.product_id.invoice_policy
            or line.state != "sale"
            or not line.order_id.invoice_policy_required
        )
        super(SaleOrderLine, other_lines)._compute_untaxed_amount_to_invoice()
        for line in self - other_lines:
            invoice_policy = line.order_id.invoice_policy
            amount_to_invoice = 0.0
            uom_qty_to_consider = (
                line.qty_delivered
                if invoice_policy == "delivery"
                else line.product_uom_qty
            )
            price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            price_subtotal = price_reduce * uom_qty_to_consider
            if any(line.tax_ids.mapped("price_include")):
                price_subtotal = line.tax_ids.compute_all(
                    price_reduce,
                    currency=line.currency_id,
                    quantity=uom_qty_to_consider,
                    product=line.product_id,
                    partner=line.order_id.partner_shipping_id,
                )["total_excluded"]
            inv_lines = line._get_invoice_lines()
            if any(inv_lines.mapped(lambda l: l.discount != line.discount)):
                amount = 0
                for inv_line in inv_lines:
                    converted_price = inv_line.currency_id._convert(
                        inv_line.price_unit,
                        line.currency_id,
                        line.company_id,
                        inv_line.date or fields.Date.today(),
                        round=False,
                    )
                    if any(inv_line.tax_ids.mapped("price_include")):
                        amount += inv_line.tax_ids.compute_all(
                            converted_price,
                            currency=line.currency_id,
                            quantity=inv_line.quantity,
                            product=inv_line.product_id,
                            partner=inv_line.partner_id,
                        )["total_excluded"]
                    else:
                        amount += converted_price * inv_line.quantity
                amount_to_invoice = max(price_subtotal - amount, 0)
            else:
                amount_to_invoice = price_subtotal - line.untaxed_amount_invoiced
            line.untaxed_amount_to_invoice = amount_to_invoice
        return True
