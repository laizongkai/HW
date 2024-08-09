from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from jose import jwt, JWTError
from typing import List, Annotated
from datetime import timedelta, datetime, timezone
from passlib.context import CryptContext
from jwt.exceptions import InvalidTokenError
from starlette import status
import models
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel

import jwt 
#import auth

app = FastAPI()
#app.include_router(auth.router)

app.mount("/static", StaticFiles(directory="../fronted/static"), name="static")
templates = Jinja2Templates(directory = "../fronted/templates")

models.Base.metadata.create_all(bind = engine)

bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

#JWT Secret and Algorithm
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1

def get_db():
    db = SessionLocal()
    try:
        yield db
    
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    
    return templates.TemplateResponse(
        request = request, name="index.html"  
    )

#檢查是否有該使用者
def get_mail_by_database(db:Session, email:str):
    #無該表回傳False
    try: 
        return db.query(models.Users).filter(models.Users.email == email).first()
    except:
        return False
    
class RegisterUserBase(BaseModel):
    username:str
    email:str
    password:str

#建立使用者
@app.post("/users")
async def create_user(request: RegisterUserBase, db: db_dependency):
    
    print(request.username)
    print(request.email)
    print(request.password)
    
    db_mail = get_mail_by_database(db, email = request.email)
    
    if db_mail:
        raise HTTPException(status_code = 400, detail = "Email already registered ")
    
    else:
        now_time = datetime.now(timezone.utc)
        now_time = now_time.strftime("%Y-%m-%d")
        
        db_user = models.Users(username = request.username, email = request.email, register_date = now_time)
        db.add(db_user)
        db.commit()
        
        create_JWT_password(db, email = request.email, password = request.password)
        
        raise HTTPException(status_code = 200, detail = "Register Success")
    
#創建JWT密碼
def create_JWT_password(db:Session,  email:str, password:str ):
    create_user_model = models.ConfirmUsers(
        email = email,
        hash_password = bcrypt_context.hash(password)
    )
    db.add(create_user_model)
    db.commit()


class LoginUserBase(BaseModel):
    email:str
    password:str
    

#登入
@app.post("/login")     
def login_for_access_token(request:LoginUserBase, db:Session = Depends(get_db)):     
    print(request.email, request.password)
    user = authenticate_user(request.email, request.password, db)
    if not user:
        
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED, 
            detail = "Incorrect username or password",
            headers = {"WWW-Authenticate":"Bearer"}
        )
        
    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub":request.email}, expires_delta = access_token_expires 
    )
    #return Token(access_token=access_token, token_type="bearer")
    return {"status_code":200, "access_token":access_token, "token_type":"bearer", "detail":"Login Success"}

#認證
def authenticate_user(email, password, db:Session):
    user = db.query(models.ConfirmUsers).filter(email == models.ConfirmUsers.email).first()

    if not user:
        return False
    
    if not bcrypt_context.verify(password, user.hash_password):
        return False
    
    return user
   
#產生jwt
def create_access_token(data:dict, expires_delta:timedelta | None = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes = 15)
    
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)
    return encoded_jwt


class Token(BaseModel):
    access_token: str
    token_type: str

# 獲取 Authorize 表單資訊(username、password)
@app.post("/token", response_model = Token)
async def access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect username or password",
            headers = {"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": user.email}, expires_delta = access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
    

class TokenData(BaseModel):
    email: str | None = None

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "None")
        
    except InvalidTokenError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Token Error")

    return {"email":email}
    
        
class User(BaseModel):
    email: str
    disabled: bool | None = None


@app.get("/users", status_code = status.HTTP_200_OK)
async def get_all_users_information(current_user: Annotated[User, Depends(get_current_user)], db:Session = Depends(get_db)):
    result = db.query(models.Users).all()
    
    if result is None:
        raise HTTPException(status_code = 404, detail = " No Table !")
    
    else:
        return result

@app.get("/users/{user_id}", status_code = status.HTTP_200_OK)
async def get_users_information(user_id:int, current_user: Annotated[User, Depends(get_current_user)], db:Session = Depends(get_db)):
    result = db.query(models.Users).filter(models.Users.id == user_id).first()
    if result is None:
        raise HTTPException(status_code = 404, detail = " No Data !")
    
    else:
        return result

class UpdateUserBase(BaseModel):
    username:str

@app.put("/users/{user_id}", status_code = status.HTTP_200_OK)
async def update_users_information(user_id:int, request: UpdateUserBase, current_user: Annotated[User, Depends(get_current_user)], db:Session = Depends(get_db)):
    result = db.query(models.Users).filter(models.Users.id == user_id).first()
    
    if result is None: 
        raise HTTPException(status_code = 404, detail = " No Data !")
    
    else:
        result.username = request.username
        db.commit()
          
    return result.username

@app.delete("/users/{user_id}", status_code = status.HTTP_200_OK)
async def delete_users(user_id:int, current_user: Annotated[User, Depends(get_current_user)], db:Session = Depends(get_db)):
    result = db.query(models.Users).filter(models.Users.id == user_id).first()
    if result is None:
        raise HTTPException(status_code = 404, detail = " No Data !")
    else:
        db.delete(result)
        db.commit()