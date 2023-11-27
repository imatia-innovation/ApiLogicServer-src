from api.system.custom_endpoint import CustomEndpoint, DotDict
from database import models
from flask import request, jsonify
from sqlalchemy import Column

class Order(CustomEndpoint):
    def __init__(self):
        order = super(Order, self).__init__(
            model_class=models.Order
            , alias = "order"
            # , role_name = "OrderList"
            # , join_on=models.Order.CustomerId
            , fields = [models.Order.Id, (models.Order.AmountTotal, "Total"), (models.Order.OrderDate, "Order Date"), models.Order.Ready]
            , children = CustomEndpoint(model_class=models.OrderDetail, alias="Items"
                , join_on=models.OrderDetail.OrderId
                , fields = [models.OrderDetail.OrderId, models.OrderDetail.Quantity, models.OrderDetail.Amount]
                , children = CustomEndpoint(model_class=models.Product, alias="product"
                    , join_on=models.OrderDetail.ProductId
                    , fields=[models.Product.ProductName, models.Product.UnitPrice, models.Product.UnitsInStock]
                    , isParent=True
                    , isCombined=False
                )
            )
        )

        # CustomEndpoint(model_class=models.OrderAudit, alias="orderAudit")  # sibling child
        return order
    
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
        row_as_dict = {}  # using row fails, eg, Decimal('1.0')
        row_attrs = row._s_jsonapi_attrs
        for each_field in custom_endpoint.fields:
            if isinstance(each_field, tuple):       # alias
                row_as_dict[each_field[1]] = row_attrs[each_field[0].name]
            else:
                if isinstance(each_field, str):     # use attr name
                    print("Coding error - you need to use TUPLE for attr/alias")
                row_as_dict[each_field.name] = row_attrs[each_field.name]
        
        list_of_children = custom_endpoint.children
        if isinstance(list_of_children, list) is False:
            list_of_children = []
            list_of_children.append(custom_endpoint.children)
        for each_child_def in list_of_children:
            child_property_name = each_child_def.role_name
            if child_property_name == '':
                child_property_name = "OrderList"  # FIXME default from class name
            if child_property_name.startswith('Product'):
                debug = 'good breakpoint'
            all_children = getattr(row, child_property_name)
            row_as_dict[each_child_def.alias] = []
            if each_child_def.isParent:
                the_parent = getattr(row, child_property_name)
                the_parent_to_dict = self.to_dict(row = the_parent, current_endpoint = each_child_def)
                row_as_dict[each_child_def.alias].append(the_parent_to_dict)
            else:
                for each_child in all_children:
                    each_child_to_dict = self.to_dict(row = each_child, current_endpoint = each_child_def)
                    row_as_dict[each_child_def.alias].append(each_child_to_dict)
        return row_as_dict
