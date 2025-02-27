from ..handlers.msg.messages import department_msg, branch_msg, type_msg, period_msg, menu_msg, test_msg


layout = {
    "enter_department": [
        department_msg, 
        branch_msg
    ],
    "revenue": [
        lambda msg_data: period_msg(msg_data, [0, 1, 2, 3, 4, 5, 6]), 
        lambda msg_data: menu_msg(msg_data, [0, 1, 2, 4])
    ],
    "write-off": [

    ],
    "losses": [
        lambda msg_data: type_msg(msg_data, [0, 1]), 
        lambda msg_data: period_msg(msg_data, [2, 3, 5]), 
        lambda msg_data: menu_msg(msg_data, [0, 2, 4])
    ],
    "foodcost": [
        lambda msg_data: type_msg(msg_data, [2]), 
        lambda msg_data: period_msg(msg_data, [1, 2, 3, 4, 5, 6]), 
        lambda msg_data: menu_msg(msg_data, [0, 1, 3, 4])
    ],
    "turnover": [
        lambda msg_data: period_msg(msg_data, [1, 2, 3, 4, 5, 6]), 
        lambda msg_data: menu_msg(msg_data, [0, 1, 2, 4])
    ],
}
