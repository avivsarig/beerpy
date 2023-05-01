import re


def response_from_error(e: str) -> tuple[int, str]:
    if "not-null constraint" in str(e).lower():
        field = str(e).split('"')[1].capitalize()
        model = str(e).split('"')[3].capitalize()
        message = f"{model} must have a {field}"
        return 400, message

    elif "unique constraint" in str(e).lower():
        value = str(e).split("(")[2].split(")")[0]
        field = str(e).split("(")[1].split(")")[0]
        message = f"The {field}: {value} already exists"
        return 400, message

    elif "check constraint" in str(e).lower():
        if "beers_abv" in str(e).lower():
            message = "A beer ABV cannot be negative"
        elif "beers_price" in str(e).lower():
            message = "A beer price cannot be negative"
        else:
            message = "Check constraint violation"
        return 400, message

    elif "foreign key constraint" in str(e).lower():
        print(str(e).lower())
        if "users" in str(e).lower():
            key = "user"
        if "beers" in str(e).lower():
            key = "beer"
        id = str(e).split("(")[2].split(")")[0]
        return 400, f"No {key} with id {id} found"

    else:
        return 500, "Internal Error"
