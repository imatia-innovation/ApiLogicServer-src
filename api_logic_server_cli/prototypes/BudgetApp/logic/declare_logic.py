import datetime
from decimal import Decimal
from logic_bank.exec_row_logic.logic_row import LogicRow
from logic_bank.extensions.rule_extensions import RuleExtension
from logic_bank.logic_bank import Rule
from database import models
import api.system.opt_locking.opt_locking as opt_locking
import logging
from security.system.authorization import Grant

app_logger = logging.getLogger(__name__)

def declare_logic():
    ''' Declarative multi-table derivations and constraints, extensible with Python. 

    Brief background: see readme_declare_logic.md
    
    Use code completion (Rule.) to declare rules here:
    '''

    def handle_all(logic_row: LogicRow):  # OPTIMISTIC LOCKING, [TIME / DATE STAMPING]
        """
        This is generic - executed for all classes.

        Invokes optimistic locking.

        You can optionally do time and date stamping here, as shown below.

        Args:
            logic_row (LogicRow): from LogicBank - old/new row, state
        """
        if logic_row.is_updated() and logic_row.old_row is not None and logic_row.nest_level == 0:
            opt_locking.opt_lock_patch(logic_row=logic_row)
        enable_creation_stamping = False  # CreatedOn time stamping
        if enable_creation_stamping:
            row = logic_row.row
            if logic_row.ins_upd_dlt == "ins" and hasattr(row, "CreatedOn"):
                row.CreatedOn = datetime.datetime.now()
                logic_row.log("early_row_event_all_classes - handle_all sets 'Created_on"'')
        Grant.process_updates(logic_row=logic_row)

    Rule.early_row_event_all_classes(early_row_event_all_classes=handle_all)

    # Roll up budget amounts
    Rule.sum(derive=models.BudgetYr.budget_total, as_sum_of=models.BudgetQtr.budget_total)
    Rule.sum(derive=models.BudgetQtr.budget_total, as_sum_of=models.BudgetMonth.budget_total)
    Rule.sum(derive=models.BudgetMonth.budget_total, as_sum_of=models.Budget.amount)
    Rule.copy(derive=models.Budget.is_expense,from_parent=models.Category.is_expense)
    
    # Roll up actual transaction amounts
    Rule.sum(derive=models.BudgetYr.actual_amount, as_sum_of=models.BudgetQtr.actual_amount)
    Rule.sum(derive=models.BudgetQtr.actual_amount, as_sum_of=models.BudgetMonth.actual_amount)
    Rule.sum(derive=models.BudgetMonth.actual_amount, as_sum_of=models.Transaction.amount)
    Rule.copy(derive=models.Transaction.is_expense,from_parent=models.Category.is_expense)
    
    app_logger.debug("..logic/declare_logic.py (logic == rules + code)")
