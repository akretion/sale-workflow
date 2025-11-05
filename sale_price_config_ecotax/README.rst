Sale Price Config Ecotax
========================

This addon adds the product ecotax amount to the price computed by
``sale_price_config``.

Behavior
--------

- When pricing is computed via ``sale_price_config`` (context contains
  ``price_config`` and ``input_line``), the module adds ``product.ecotax_amount``
  from ``account_ecotax`` to the computed price.
- Outside that flow, pricing is unchanged.

Dependencies
------------

- sale_price_config
- account_ecotax

License
-------

AGPL-3

