============================
Sale Invoice Policy Extended
============================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/license-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/odoo-19.0-714B67.png
    :alt: Odoo 19.0

|badge1| |badge2| |badge3|

This module lets you choose an invoicing policy on the **sale order**
itself rather than letting the per-product policy decide. It is a fork
of the OCA `sale_invoice_policy
<https://github.com/OCA/sale-workflow/tree/18.0/sale_invoice_policy>`_
module with additional features around partner defaults, mandatory
enforcement, and bulk maintenance.

**Table of contents**

.. contents::
   :local:

What this module does
=====================

On every sale order you can pick how the order should be invoiced:

- **Ordered Quantities** — invoice the quantities the customer ordered.
- **Delivered Quantities** — invoice the quantities actually delivered.
- *Empty* — fall back to each product's own invoicing policy
  (standard Odoo behaviour).

The chosen policy drives both the *quantity to invoice* and the
*untaxed amount to invoice* on every line of the order, including the
edge cases where an order has been partially invoiced or the order
contains products with a different per-product policy.

Differences vs. OCA ``sale_invoice_policy``
===========================================

This fork keeps the core idea of the upstream OCA module (an order-level
invoice policy) but adds the following on top.

Per-partner default invoice policy
----------------------------------

A new field ``default_invoice_policy`` is added to **res.partner** (only
visible on company contacts). When you create a new sale order for that
customer, the order's ``invoice_policy`` is pre-filled from the partner.

Upstream OCA only supports a single global default per company; this
fork supports a per-customer default that overrides the global one.

Mandatory invoice policy on sale orders
---------------------------------------

A new setting under *Sales → Configuration → Settings* —
**Sale Invoice Policy** — toggles whether the invoice policy field is
**required** on every sale order. When enabled, the salesperson cannot
confirm the order without explicitly choosing a policy.

Upstream OCA leaves the field optional in all cases.

Bulk "Set Default Invoice Policy" server action
-----------------------------------------------

A server action is exposed on the partner list view (Action menu →
*Set Default Invoice Policy*) that backfills the per-partner default on
all selected company partners that don't have one yet. Useful after
installing the module on an existing database.

Simpler dependency tree
-----------------------

This fork depends on ``sale_stock``, ``sale`` and ``account`` only.
Upstream OCA additionally requires ``base_partition`` and the external
Python package ``openupgradelib`` (used by its ``pre_init_hook``); this
fork avoids both, so installation does not require any extra pip
package.

Two-state selection
-------------------

The field uses the two values ``order`` and ``delivery``. Leaving the
field blank gives you the standard "use product policy" behaviour.
Upstream OCA exposes the same effect with a third explicit selection
value.

Configuration
=============

After installing the module:

1. Go to *Sales → Configuration → Settings*.
2. Under **Sale Invoice Policy**, decide whether the invoice policy
   should be required on every sale order.
3. (Optional) Open a customer's contact form and set
   *Default Invoicing Policy* on the *Sales & Purchase* tab, or use the
   *Set Default Invoice Policy* server action from the partner list to
   backfill in bulk.

Usage
=====

1. Create a Sale Order.
2. The *Invoice Policy* field is pre-filled from the partner's default
   (if any). Adjust per-order if needed.
3. Confirm the order and create invoices as usual — quantities and
   amounts will follow the chosen policy regardless of each product's
   own configuration.

Compatibility
=============

- Odoo **19.0** Enterprise / Community.
- Migrated from OCA ``sale_invoice_policy_extended`` 16.0; ported
  through 17/18 changes (``attrs``/``states`` removal, ``ir.default``
  private API, ``tax_id`` → ``tax_ids``, ``price_reduce`` removal,
  ``has_group`` singleton enforcement, settings ``<setting>`` element).

Bug Tracker
===========

Issues with **this fork** should be reported on this repository's
GitHub Issues page.

For issues that reproduce on stock OCA ``sale_invoice_policy``, please
report them upstream at
https://github.com/OCA/sale-workflow/issues.

Credits
=======

Authors
-------

* ACSONE SA/NV (original ``sale_invoice_policy`` and
  ``sale_invoice_policy_extended``)

Contributors
------------

Upstream OCA contributors:

- Cédric Pigeon <cedric.pigeon@acsone.eu>
- François Honoré <francois.honore@acsone.eu>
- Denis Roussel <denis.roussel@acsone.eu>
- Alexei Rivera <arivera@archeti.com>
- Luis J. Salvatierra <luis.salvatierra@factorlibre.com>
- Alejandro Ji Cheung <alejandro.jicheung@factorlibre.com>
- Ioan Galan <ioan@studio73.es>

Fork / 19.0 migration:

- LASSE Larsson <lasse@familjenlarsson.eu>

License
=======

AGPL-3. See the LICENSE file shipped with the upstream OCA repository
or http://www.gnu.org/licenses/agpl-3.0-standalone.html for the full
text.

This module is a derivative work of OCA ``sale_invoice_policy`` and
inherits the same AGPL-3 license.
