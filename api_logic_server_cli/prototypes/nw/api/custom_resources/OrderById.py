from api.system.custom_endpoint import CustomEndpoint
from database import models
from flask import request, jsonify
from sqlalchemy import Column

class OrderById(CustomEndpoint):
    def __init__(self):
        """TODO

        Returns:
            _type_: _description_
        """
        order = super(OrderById, self).__init__(
            model_class=models.Order
            , alias = "order"
            # , role_name = "OrderList"
            # , join_on=models.Order.CustomerId
            , fields = (models.Order.CustomerId, "AccountId")
            , children = CustomEndpoint(model_class=models.OrderDetail, alias="Items"
                , join_on=models.OrderDetail.OrderId
                , fields = [(models.OrderDetail.Quantity, "QuantityOrdered"), (models.OrderDetail.ProductId, "ProductId")]
            )
        )

        # CustomEndpoint(model_class=models.OrderAudit, alias="orderAudit")  # sibling child
        return order
