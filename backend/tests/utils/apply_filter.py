import operator
from datetime import datetime


def apply_filter(data_list, field, op, value):
    filtered_data = []
    if field not in data_list[0].keys():
        return data_list

    if op == "":
        op = "[eq]"

    operators = {
        "[lt]": operator.lt,
        "[le]": operator.le,
        "[eq]": operator.eq,
        "[ge]": operator.ge,
        "[gt]": operator.gt,
    }

    if field == "date_of_arrival":
        value = datetime.isoformat(value)

    for data in data_list:
        if field == "date_of_arrival":
            data[field] = datetime.fromisoformat(data[field]).isoformat()
            
        if operators[op](data[field], value):
            filtered_data.append(data)

    return filtered_data
