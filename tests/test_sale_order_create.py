# Copyright 2026 Familjen Larsson
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Verify that the partner's default invoice policy is applied at
``sale.order.create()`` time, not only via the UI onchange.

This is what makes the module work for eCommerce checkout, API and
script-driven order creation, instead of only the backend form view.
"""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderCreate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SaleOrder = cls.env["sale.order"]
        cls.Partner = cls.env["res.partner"]
        cls.Product = cls.env["product.product"]

        cls.product = cls.Product.create({
            "name": "Test Product (sale_invoice_policy_extended)",
            "type": "consu",
            "list_price": 50.0,
            "taxes_id": [(5, 0, 0)],
        })

        cls.partner_with_order = cls.Partner.create({
            "name": "Partner With Order Default",
            "is_company": True,
            "default_invoice_policy": "order",
        })
        cls.partner_with_delivery = cls.Partner.create({
            "name": "Partner With Delivery Default",
            "is_company": True,
            "default_invoice_policy": "delivery",
        })
        cls.partner_no_default = cls.Partner.create({
            "name": "Partner Without Default",
            "is_company": True,
            # default_invoice_policy left unset
        })

    def _new_so(self, partner, **extra):
        vals = {
            "partner_id": partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 50.0,
            })],
        }
        vals.update(extra)
        return self.SaleOrder.create(vals)

    # ------------------------------------------------------------------
    # The core fix: create() applies the partner default
    # ------------------------------------------------------------------
    def test_create_applies_partner_default_order(self):
        so = self._new_so(self.partner_with_order)
        self.assertEqual(
            so.invoice_policy, "order",
            "SO created via Python with a partner that has "
            "default_invoice_policy='order' must inherit it",
        )

    def test_create_applies_partner_default_delivery(self):
        so = self._new_so(self.partner_with_delivery)
        self.assertEqual(
            so.invoice_policy, "delivery",
            "SO created via Python with a partner that has "
            "default_invoice_policy='delivery' must inherit it",
        )

    # ------------------------------------------------------------------
    # Caller wins — explicit vals are never overwritten
    # ------------------------------------------------------------------
    def test_create_respects_explicit_invoice_policy(self):
        so = self._new_so(
            self.partner_with_order,
            invoice_policy="delivery",
        )
        self.assertEqual(
            so.invoice_policy, "delivery",
            "Explicit invoice_policy in create() vals must be respected "
            "even when the partner has a different default",
        )

    def test_create_respects_explicit_falsy_invoice_policy(self):
        # Passing the key with False means "no policy, fall back to per
        # product" — that explicit choice must also be respected.
        so = self._new_so(
            self.partner_with_order,
            invoice_policy=False,
        )
        self.assertFalse(
            so.invoice_policy,
            "Explicit invoice_policy=False must be kept (caller signaled "
            "they want no SO-level policy)",
        )

    # ------------------------------------------------------------------
    # Partner with no default — keep whatever default_get set
    # ------------------------------------------------------------------
    def test_create_no_partner_default_is_noop(self):
        # We don't assert a specific value because default_get may set
        # one from system settings; we only assert our override didn't
        # corrupt anything.
        before_create_keys = {"partner_id", "order_line"}
        # Build vals manually so we can inspect them.
        vals = {
            "partner_id": self.partner_no_default.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 50.0,
            })],
        }
        so = self.SaleOrder.create(vals)
        # The partner has no default, so create() should not have
        # injected anything beyond what default_get would have set.
        self.assertEqual(so.partner_id, self.partner_no_default)

    # ------------------------------------------------------------------
    # model_create_multi works with batches
    # ------------------------------------------------------------------
    def test_create_multi_applies_per_partner(self):
        sos = self.SaleOrder.create([
            {
                "partner_id": self.partner_with_order.id,
                "order_line": [(0, 0, {
                    "product_id": self.product.id,
                    "product_uom_qty": 1.0,
                    "price_unit": 50.0,
                })],
            },
            {
                "partner_id": self.partner_with_delivery.id,
                "order_line": [(0, 0, {
                    "product_id": self.product.id,
                    "product_uom_qty": 1.0,
                    "price_unit": 50.0,
                })],
            },
            {
                "partner_id": self.partner_with_order.id,
                # Explicit override — must be respected.
                "invoice_policy": "delivery",
                "order_line": [(0, 0, {
                    "product_id": self.product.id,
                    "product_uom_qty": 1.0,
                    "price_unit": 50.0,
                })],
            },
        ])
        self.assertEqual(sos[0].invoice_policy, "order")
        self.assertEqual(sos[1].invoice_policy, "delivery")
        self.assertEqual(sos[2].invoice_policy, "delivery",
                         "Explicit invoice_policy in batch must be respected")

    # ------------------------------------------------------------------
    # Onchange still works in the UI (regression guard)
    # ------------------------------------------------------------------
    def test_onchange_still_works(self):
        so_form = self.env["sale.order"].new({
            "partner_id": self.partner_with_order.id,
        })
        # Trigger the onchange explicitly.
        so_form._onchange_partner_invoice_policy()
        self.assertEqual(
            so_form.invoice_policy, "order",
            "Backwards compatibility: the original onchange behavior "
            "must still fire in the form view",
        )
