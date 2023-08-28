def response_from_error(e) -> tuple[int, str]:
    error_string = str(e)
    if "not-null constraint" in error_string.lower():
        field = error_string.split('"')[1].capitalize()
        model = error_string.split('"')[3].capitalize()
        message = f"{model} must have a {field}"
        return 400, message

    elif "unique constraint" in error_string.lower():
        value = error_string.split("(")[2].split(")")[0]
        field = error_string.split("(")[1].split(")")[0]
        message = f"The {field}: {value} already exists"
        return 400, message

    else:
        return 500, "Internal Error"
