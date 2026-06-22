from fastapi import HTTPException, status

# ----- User -----

user_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "User not found"
)

no_rights_exception = HTTPException(
    status.HTTP_403_FORBIDDEN,
    "You have no rights to perform this action"
)

email_registered_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST,
    "Email is used by another user"
)


# ----- App -----

app_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "Application not found"
)

apps_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "No applications found"
)

app_not_purchased_exception = HTTPException(
    status.HTTP_402_PAYMENT_REQUIRED,
    "Application must be purchased"
)

not_enough_funds_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST,
    "You don't have sufficient funds to complete the transaction"
)


# ----- Comment -----

review_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "Review not found"
)
