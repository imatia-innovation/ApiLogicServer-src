from api.system.custom_endpoint import CustomEndpoint, DotDict
from database import models
from flask import request, jsonify
from sqlalchemy import Column

class Customer(CustomEndpoint):
    def __init__(self):
        customer = super(Customer, self).__init__(
            model_class=models.Customer
            , alias="customers"
            , fields = [(models.Customer.CompanyName, "Customer Name")] 
            , children = [
                CustomEndpoint(model_class=models.Order
                    , alias = "orders"
                    , join_on=models.Order.CustomerId
                    , fields = [(models.Order.AmountTotal, "Total"), (models.Order.ShippedDate, "Ship Date")]
                    , children = [CustomEndpoint(model_class=models.OrderDetail, alias="details"
                        , join_on=models.OrderDetail.OrderId
                        , fields = [models.OrderDetail.Quantity, models.OrderDetail.Amount]
                        , children = [CustomEndpoint(model_class=models.Product, alias="product"
                            , join_on=models.OrderDetail.ProductId
                            , fields=[models.Product.UnitPrice, models.Product.UnitsInStock]
                            , isParent=True
                            , isCombined=False
                        )]
                    )]
                )
                ]
        # CustomEndpoint(model_class=models.OrderAudit, alias="orderAudit")  # sibling child
        )
        return customer
    
    def to_dict(self, row: object, current_endpoint: CustomEndpoint = None) -> dict:
        """returns row as dict per custom resource definition, with subobjects

        Args:
            row (_type_): a SQLAlchemy row

        Returns:
            dict: row formatted as dict
        """
        custom_endpoint = self
        if current_endpoint is not None:
            custom_endpoint = current_endpoint
        # row_as_dict = self.row_to_dict(row)
        row_as_dict = {}
        for each_field in custom_endpoint.fields:
            if isinstance(each_field, tuple):
                row_as_dict[each_field[0].name] = getattr(row, each_field[0].name)
            else:
                if isinstance(each_field, str):
                    print("Coding error - you need to use TUPLE for attr/alias")
                row_as_dict[each_field.name] = getattr(row, each_field.name)
        
        for each_child_def in custom_endpoint.children:
            child_property_name = "OrderList"  # FIXME this should be in CustomEndpoint
            all_children = getattr(row, child_property_name)
            row_as_dict[child_property_name] = []
            for each_child in all_children:
                each_child_to_dict = self.to_dict(row = each_child, current_endpoint = each_child_def)
                row_as_dict[child_property_name].append(each_child_to_dict)
        return row_as_dict
