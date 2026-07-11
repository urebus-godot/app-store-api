from fastapi import HTTPException, status

# ----- User -----

user_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, "User not found"
)

no_rights_exception = HTTPException(
    status.HTTP_403_FORBIDDEN, "You have no rights to perform this action"
)

email_used_exception = HTTPException(
    status.HTTP_409_CONFLICT, "Email is used by another user"
)

username_used_exception = HTTPException(
    status.HTTP_409_CONFLICT, "Username is used by another user"
)

user_data_used_exception = HTTPException(
    status.HTTP_409_CONFLICT, "Username or email is already used"
)

already_has_role_exception = HTTPException(
    status.HTTP_409_CONFLICT, "You already have the requested role"
)

not_positive_amount_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST, "Amount must be positive"
)


# ----- Authentication -----

incorrect_creds_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)

invalid_refresh_token_exception = HTTPException(
    status.HTTP_401_UNAUTHORIZED, "Invalid refresh token"
)

invalid_access_token_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
)

invalid_token_payload_exception = HTTPException(
    status.HTTP_401_UNAUTHORIZED, "Invalid token payload"
)


# ----- App -----

app_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, "Application not found"
)

apps_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, "No applications found"
)

app_not_purchased_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST, "Application must be purchased"
)

not_enough_funds_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST,
    "You don't have sufficient funds to complete the transaction",
)


# ----- Cart -----

app_purchased_exception = HTTPException(
    status.HTTP_409_CONFLICT, "Application has already been purchased"
)

app_in_cart_exception = HTTPException(
    status.HTTP_409_CONFLICT, "Application has already been added to the cart"
)

app_published_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST, "Application is published by you"
)

empty_cart_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST, "Cart is empty"
)

app_not_in_cart_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, "Application not in the cart"
)


# ----- Comment -----

review_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, "Review not found"
)


# ----- Discussion ------

message_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, "Message not found"
)

discussion_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, "Discussion not found"
)
