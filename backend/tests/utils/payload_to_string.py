def payload_to_string(data, keys_order=None):
    if keys_order is None:
        keys_order = list(data.keys())
    return ", ".join(["'{}'".format(data[key]) for key in keys_order])
