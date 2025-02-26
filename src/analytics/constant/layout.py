from ..handlers.msg.messages import department_msg, branch_msg, type_msg, period_msg, test_msg


layout = {
    "enter_department": [
        department_msg, 
        branch_msg
    ],
    "revenue": [

    ],
    "write-off": [

    ],
    "losses": [
        lambda m: type_msg(m, [0, 1]), 
        lambda m: period_msg(m, [0, 1, 2, 3]), 
        test_msg
    ],
    "food-cost": [

    ],
    "turnover": [

    ],
}
