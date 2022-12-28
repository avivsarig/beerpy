import operator
import urllib


def query_to_filters(raw_query_string: str):
    query_string = urllib.parse.unquote(raw_query_string, encoding="utf-8")
    query_list = query_string.split("&")
    if query_list[0] == "":
        return []

    operators = {
        "lt": operator.lt,
        "le": operator.le,
        "eq": operator.eq,
        "ge": operator.ge,
        "gt": operator.gt,
    }

    filters = []
    for item in query_list:
        field, value = item.split("=")
        if field in ["page", "sort", "limit", "fields"]:
            break
        op = "eq"
        if ("[" in field) and ("]" in field):
            field, op = field.split("[")
            op = op[:-1]

        filters.append({"field": field, "value": value, "op": operators[op]})

    return filters
