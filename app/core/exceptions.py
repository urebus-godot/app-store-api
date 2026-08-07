from fastapi import HTTPException, status


# ----- General -----

too_many_requests_exception = HTTPException(
    status.HTTP_429_TOO_MANY_REQUESTS,
    "Request limit exceeded. Try again later",
    {"X-RateLimit-Remaining": "0"}
)

no_rights_exception = HTTPException(
    status.HTTP_403_FORBIDDEN, "You have no rights to perform this action"
)

# ----- Storage ------

invalid_file_exception = HTTPException(
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    "Invalid type of file"
)

file_too_large_exception = HTTPException(
    status.HTTP_413_CONTENT_TOO_LARGE,
    "Uploaded file size is too large"
)

file_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "File not found in storage"
)

no_load_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "No data in storage to confirm"
)


# ----- User -----

user_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, 
    "User not found"
)

email_used_exception = HTTPException(
    status.HTTP_409_CONFLICT, 
    "Email is used by another user"
)

username_used_exception = HTTPException(
    status.HTTP_409_CONFLICT, 
    "Username is used by another user"
)

user_data_used_exception = HTTPException(
    status.HTTP_409_CONFLICT, 
    "Username or email is already used"
)

already_has_role_exception = HTTPException(
    status.HTTP_409_CONFLICT, 
    "You already have the requested role"
)

not_positive_amount_exception = HTTPException(
    status.HTTP_422_UNPROCESSABLE_CONTENT, 
    "Amount must be positive"
)

no_profile_pic_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST,
    "Profile picture is not set"
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
    status.HTTP_401_UNAUTHORIZED, 
    "Invalid access token"
)

invalid_token_payload_exception = HTTPException(
    status.HTTP_401_UNAUTHORIZED, 
    "Invalid token payload"
)


# ----- App -----

app_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, 
    "Application not found"
)

app_not_purchased_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST, 
    "Application must be purchased"
)

insufficient_funds_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST,
    "Insufficient funds",
)

app_cover_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "App cover not found"
)


# ----- Purchase -----

app_purchased_exception = HTTPException(
    status.HTTP_409_CONFLICT, 
    "Application has already been purchased"
)

app_in_cart_exception = HTTPException(
    status.HTTP_409_CONFLICT, 
    "Application has already been added to the cart"
)

app_published_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST, 
    "Application is published by you"
)

empty_cart_exception = HTTPException(
    status.HTTP_400_BAD_REQUEST, 
    "Cart is empty"
)

cart_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, 
    "Cart not found"
)

app_not_in_cart_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, 
    "Application not in the cart"
)


# ----- Review -----

review_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, 
    "Review not found"
)


# ----- Discussion ------

message_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, 
    "Message not found"
)

discussion_not_found_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, 
    "Discussion not found"
)


# ------ Promo code -----

invalld_promo_code_exception = HTTPException(
    status.HTTP_404_NOT_FOUND, 
    "Promo code has expired or is invalid"
)