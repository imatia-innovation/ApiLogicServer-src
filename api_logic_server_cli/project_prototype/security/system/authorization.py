"""
System support for role based authorization.

Supports declaring grants,
and enforcing them using SQLAlchemy 
   * do_orm_execute
   * with_loader_criteria(each_grant.entity, each_grant.filter)

You typically do not alter this file.
"""

from typing import Dict, Tuple
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import session
from sqlalchemy import event, MetaData, and_, or_
import safrs
from sqlalchemy import event, MetaData
from sqlalchemy.orm import with_loader_criteria, DeclarativeMeta
import logging, sys
<<<<<<< HEAD
from safrs.errors import JsonapiError
from http import HTTPStatus
<<<<<<< HEAD
=======
=======
>>>>>>> c72778a (Revert "merge latest security")


>>>>>>> fc01c21 (merge latest security)
from flask_jwt_extended import current_user

from config import Args
authentication_provider = Args.security_provider

security_logger = logging.getLogger(__name__)

security_logger.debug(f'\nAuthorization loaded via api_logic_server_run.py -- import \n')


db = safrs.DB         # Use the safrs.DB, not db!
session = db.session  # sqlalchemy.orm.scoping.scoped_session


class Security:

    @classmethod
    def set_user_sa(cls):
        from flask import g
        g.isSA = True

    @classmethod
    def current_user(cls):
        """ 
        User code calls this as required to get user/roles (eg, multi-tenant client_id)

        see https://flask-login.readthedocs.io/en/latest/
        """
        return current_user

    @staticmethod
    @classmethod
    def current_user_has_role(role_name: str) -> bool: 
        '''
        Helper, e.g. rules can determine if update allowed

        If user has role xyz, then for update authorization s/he can... 
        '''
        result = False
        for each_role in Security.current_user().UserRoleList:
            if role_name == each_role.name:
                result = True
                break
        return result
    

class Grant:
    """
    Invoke these to declare Role Permissions.

<<<<<<< HEAD
        Example
        =======
        Grant(  on_entity = models.Category,  # use code completion
                to_role = Roles.tenant,
                can_delete = False,
                can_update = False,
                can_insert = False,
                can_read = False,
<<<<<<< HEAD
                filter = models.Category.Id == Security.current_user().client_id)  # User table attributes 
=======
                filter = models.Category.Id == Security.current_user().client_id)  # User table attributes TODO
>>>>>>> fc01c21 (merge latest security)
        Args
        ----
            :on_entity: a class from models.py
            :to_role: valid role name from Authentication Provider
            :can_read: bool = True,
            :can_insert: bool = True,
            :can_update: bool = True,
            :can_delete: bool = True,
            :filter: where clause to be added
        
        per calls from declare_security.py
=======
    Use code completion to discover models.
>>>>>>> c72778a (Revert "merge latest security")
    """

    grants_by_table : Dict[str, list[object]] = {}
    '''
    Dict keyed by Table name (obtained from class name), value is a (role, filter)
    '''

    def __init__(self, on_entity: DeclarativeMeta, 
                 to_role: str = "",
                 filter: object = None):
        '''
        Create grant for <on_entity> / <to_role>

        Example
        =======
        Grant(  on_entity = models.Category,  # use code completion
                to_role = Roles.tenant,
                filter = models.Category.Id == Security.current_user().client_id)  # User table attributes
        
        Args
        ----
            on_entity: a class from models.py
            to_role: valid role name from Authentication Provider
            filter: where clause to be added
        
        per calls from declare_security.py
        '''
        self.class_name : str = on_entity._s_class_name  # type: ignore
        self.role_name : str = to_role
        self.filter = filter
<<<<<<< HEAD
        self.entity :DeclarativeMeta = on_entity 
        self.can_read = can_read
        self.can_insert = can_insert
        self.can_update = can_update
        self.can_delete = can_delete
        self.orm_execute_state = None # used by filter
        self.table_name : str = None if isinstance(on_entity, str) else on_entity.__tablename__   # type: ignore
        self.update_CRUD()
        self._entity_name:str = None if isinstance(on_entity, str) else on_entity._s_type # Class Name
        if self._entity_name is not None:
            if self._entity_name not in self.grants_by_table:
                Grant.grants_by_table[self._entity_name] = []
            Grant.grants_by_table[self._entity_name].append( self )
        else:
            if self.role_name not in self.grants_by_role:
                Grant.grants_by_role[self.role_name] = []
            Grant.grants_by_role[self.role_name].append( self )
        
        
        def current_user():
            return Security.current_user() if Args.security_enabled else None
        
    def update_CRUD(self):
<<<<<<< HEAD
        if self.class_name in ["ALL", "A", "CRUD"]:
=======
        if self.class_name in ["ALL", "A"]:
>>>>>>> fc01c21 (merge latest security)
            self._updateCRUD(True, True, True, True)
        elif self.class_name in ["None", "N"]:
            self._updateCRUD(False, False, False, False)
        elif self.class_name == "CRU":
            self._updateCRUD(True, True, True, False)
        elif self.class_name == "CU":
            self._updateCRUD(True, True, True, False)
        elif self.class_name == "U":
            self._updateCRUD(True, False, True, False)
        elif self.class_name == "D":
            self._updateCRUD(True, False, False, True)
        elif self.class_name == "C":
            self._updateCRUD(True, True, False, False)
        elif self.class_name == "R":
            self._updateCRUD(True, False, False, False)
=======
        self.entity :DeclarativeMeta = on_entity
        self.table_name : str = on_entity.__tablename__  # type: ignore
        if (self.table_name not in self.grants_by_table):
            Grant.grants_by_table[self.table_name] = []
        Grant.grants_by_table[self.table_name].append( self )
>>>>>>> c72778a (Revert "merge latest security")

    @staticmethod
    def exec_grants(orm_execute_state):
        '''
        SQLAlchemy select event for current user's roles, append that role's grant filter to the SQL before execute 

        if you have a select() construct, you can add new AND things just calling .where() again.
        
        e.g. existing_statement.where(or_(f1, f2)) .

        u2 is a manager and a tenant
        '''
<<<<<<< HEAD
<<<<<<< HEAD
=======
       
>>>>>>> fc01c21 (merge latest security)
        
        if not Args.security_enabled:
            return
        
=======
>>>>>>> c72778a (Revert "merge latest security")
        user = Security.current_user()
        mapper = orm_execute_state.bind_arguments['mapper']
        table_name = mapper.persist_selectable.fullname   # mapper.mapped_table.fullname disparaged
        try:
            from flask import g
            if g.isSA or user.id == 'sa':
                security_logger.debug("sa (eg, set_user_sa()) - no grants apply")
                return
        except:
            security_logger.debug("no user - ok (eg, system initialization)")
        if table_name in Grant.grants_by_table:
            grant_list = list()
            grant_entity = None
            for each_grant in Grant.grants_by_table[table_name]:
                grant_entity = each_grant.entity
                for each_user_role in user.UserRoleList:
                    if each_grant.role_name == each_user_role.role_name:
                        security_logger.debug(f'Amend Grant for class / role: {table_name} / {each_grant.role_name} - {each_grant.filter}')
                        grant_list.append(each_grant.filter())
            grant_filter = or_(*grant_list)
            orm_execute_state.statement = orm_execute_state.statement.options(
                with_loader_criteria(grant_entity, grant_filter ))
            security_logger.debug(f"Grants applied for {table_name}")
        else:
            security_logger.debug(f"No Grants for {table_name}")

@event.listens_for(session, 'do_orm_execute')
def receive_do_orm_execute(orm_execute_state):
    "listen for the 'do_orm_execute' event from SQLAlchemy"
    if (
        Args.security_enabled
        and orm_execute_state.is_select
        and not orm_execute_state.is_column_load
        and not orm_execute_state.is_relationship_load
    ):            
        security_logger.debug(f'receive_do_orm_execute alive')
        mapper = orm_execute_state.bind_arguments['mapper']
        table_name = mapper.persist_selectable.fullname   # mapper.mapped_table.fullname disparaged
        if table_name == "User":
            pass
            security_logger.debug(f'No grants - avoid recursion on User table')
        elif  session._proxied._flushing:  # type: ignore
<<<<<<< HEAD
            security_logger.debug('No grants during logic processing')
<<<<<<< HEAD
        else:   
=======
        else:
            #security_logger.info(f"ORM Listener table: {table_name} is_select: {orm_execute_state.is_select}")    
>>>>>>> fc01c21 (merge latest security)
            Grant.exec_grants(table_name, "is_select" , orm_execute_state)
=======
            security_logger.debug(f'No grants during logic processing')
        else:
            Grant.exec_grants(orm_execute_state) # SQL read check grants
>>>>>>> c72778a (Revert "merge latest security")
