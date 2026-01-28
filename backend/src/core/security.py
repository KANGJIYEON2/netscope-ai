from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

#  refresh token도 똑같이 해시 가능
def hash_refresh_token(refresh_token: str) -> str:
    return pwd_context.hash(refresh_token)

def verify_refresh_token(refresh_token: str, refresh_token_hash: str) -> bool:
    return pwd_context.verify(refresh_token, refresh_token_hash)