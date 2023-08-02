from security.system.authorization import Grant, Security, DefaultRolePermission
from database import models
import database
import safrs
import logging

"""
Illustrates declarative security - role-based authorization to database rows.

* See [documentation](https://apilogicserver.github.io/Docs/Security-Overview/)

<<<<<<< HEAD
* Security is invoked on server start (api_logic_server_run), per activation in `config.py

#Grant to role for specific model entity with row filter
Grant(  on_entity = models.Category,    # illustrate multi-tenant - u1 shows only row 1
        to_role = Roles.tenant,
        can_delete=False,
        filter =  lambda: models.Category.Client_id == Security.current_user().client_id)  # User table attributes

=======
* Security is invoked on server start (api_logic_server_run), per activation in `config.py`
>>>>>>> 131dd7d (wip)
"""

app_logger = logging.getLogger(__name__)

db = safrs.DB
session = db.session


class Roles():
<<<<<<< HEAD
        """ Define Roles here, so can use code completion (Roles.tenant) """
        tenant = "tenant"
        renter = "renter"
        manager = "manager"
        readonly = "readonly"
        fullaccess = "fullaccess"

# FIXME - how about a default-default?  Can I just omit the to_role?  (If so, show example).

# Configure each Role for default global permission using CRUD, All, or None
DefaultRolePermission(to_role=Roles.manager,can_read=True, can_update=True, can_insert=True,can_delete=True)
DefaultRolePermission(to_role=Roles.fullaccess,can_read=True, can_update=True, can_insert=True,can_delete=True)
DefaultRolePermission(to_role=Roles.readonly,can_read=True, can_update=False, can_insert=False,can_delete=False)
DefaultRolePermission(to_role=Roles.tenant,can_read=True, can_update=True, can_insert=False,can_delete=False)
DefaultRolePermission(to_role=Roles.renter,can_read=False, can_update=False, can_insert=False,can_delete=False)

app_logger.debug("Declare Security complete - security/declare_security.py"
        + f' -- {len(Grant.grants_by_table)} Grants by tables loaded and {len(DefaultRolePermission.grants_by_role)} Grants by role loaded.')

=======
    """ Define Roles here, so can use code completion (Roles.tenant) """
    tenant = "tenant"
    renter = "renter"
    manager = "manager"
    full_access = "fullaccess"
    read_only = "readonly"
    dev = "dev"
"""
DefaultRolePermission(to_role=Roles.tenant, can_read=True,can_insert=True,can_update=True,can_delete=False)
DefaultRolePermission(to_role=Roles.renter,can_read=True,can_insert=True,can_update=True,can_delete=False)
DefaultRolePermission(to_role=Roles.manager,can_read=True,can_insert=True,can_update=True,can_delete=False)
DefaultRolePermission(to_role=Roles.read_only, can_read=True,can_insert=False,can_update=False,can_delete=False)
DefaultRolePermission(to_role=Roles.full_access)
DefaultRolePermission(to_role=Roles.dev)


Grant(  on_entity = models.Category,    # illustrate multi-tenant - u1 shows only row 1
        to_role = Roles.tenant,
        can_delete=False,       
        filter = lambda : models.Category.Client_id == Security.current_user().client_id)  # User table attributes

Grant(  on_entity = models.Category,    # u2 has both roles - should return client_id 2 (2, 3, 4), and 5
        to_role = Roles.manager,
        filter = lambda : models.Category.Id == 5)
"""
app_logger.debug("Declare Security complete - security/declare_security.py"
    + f' -- {len(Grant.grants_by_table)} Grants by tables loaded and {len(DefaultRolePermission.grants_by_role)} Grants by role loaded.')
>>>>>>> 131dd7d (wip)
