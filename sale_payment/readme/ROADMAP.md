v18.0: removed the ability to register payments entries on sales orders.

Design decisions

- Use case A: SO is confirmed after payment is recieved.
- Use case B: SO is confirmed but MO or pickings are blocked until
  payment is recieved.
- Because of use case B, confirmed SO with invoice status not fully
  invoiced are proposed.

\- Payements and transactions are not implemented in this module to keep
simple. Transactions are coupled to e-commerce fields and payments
modules.
