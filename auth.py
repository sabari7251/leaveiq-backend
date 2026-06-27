import datetime
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def create_accessToken(data:dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXPIRE_MINUTES)

    to_encode.update({
        "exp":expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)

def get_current_user(token:str=Depends(oauth2_scheme)):

    try:
        decoded = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        email = decoded.get("sub")

        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid Token"
        )

        return decoded

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid Token"
        )
