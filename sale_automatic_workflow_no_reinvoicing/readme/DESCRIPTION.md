In case of refund on a sale order, when there was no return of merchandise, sale_automatic_workflow may automatically re-create an invoice because the sale order return to the to invoice state.
This modules aims to avoid the automatic re-invoicing in this case.
It blocks the possibility to automatically invoice more quantity than what was really shipped or ordered, it still can be manually.
The user may use an additional module like sale_force_invoiced to clean the order invoice state then.
