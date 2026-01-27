Use case: 

A payment should be received before the sale order confirmation.

Because you are unsure if the client will pay, you don't generate
transation or invoice in advance.

With this module there is an indicator on the sale order
if a payment has been received.


This module extends payment terms to add three cases:
- amount to pay before sale order confirmation
- amount to pay before preparation of the order
- amount to pay before shipping of the order

And add three booleans on sale order:
- is_so_confirmation_amount_reached
- is_preparation_confirmation_amount_reached
- is_picking_confirmation_amount_reached


Preventing the confirmation of sale order, manufacturing order or
picking is out of scope of this module.
