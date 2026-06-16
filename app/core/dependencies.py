from typing import Annotated
from fastapi import Depends, Query

def skip_limit_params(
        skip: Annotated[int, Query(lt=999)] = 0, 
        limit: Annotated[int, Query(lt=1000)] = 10,
        ):
    return skip, limit

SessionDep = Annotated[int, Depends()]
UserDep = Annotated[int, Depends()]