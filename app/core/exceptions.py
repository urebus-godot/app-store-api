from fastapi import HTTPException, status

user_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "User doesn't exists!"
)

app_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "App doesn't exists!"
)
