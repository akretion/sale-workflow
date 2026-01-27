Go to Invoicing > Payment terms

Create a new payment term: "100% at sale order"

Add a line 100%, days=0, delay: At order confirmation (no days).

Create a sale order, choose the newly created payment term.

is_so_confirmation_amount_reached on the order is false

Create an bank statement line with the amount of the sale order (so),
link this statement to the so.

is_so_confirmation_amount_reached on the order is now true.