def payload_to_string(data):
    return ", ".join(["'{}'".format(s) for s in list(data.values())])
