from backend.utils.error_handler import response_from_error


def test_not_null_constraint_error():
    error_message = 'column "name" of relation "User" violates not-null constraint'
    status_code, message = response_from_error(Exception(error_message))
    assert status_code == 400
    assert message == "User must have a Name"


def test_unique_constraint_error():
    error_message = 'duplicate key value violates unique constraint "user_email_key" (email)=(john@example.com) already exists'
    status_code, message = response_from_error(Exception(error_message))
    assert status_code == 400
    assert message == "The User Email: john@example.com already exists"


def test_generic_error():
    error_message = "some random error"
    status_code, message = response_from_error(Exception(error_message))
    assert status_code == 500
    assert message == "Internal Error"
