import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from jose import JWTError, jwt

# Import from our modular files
import database as db
import auth

# Load env variables
load_dotenv()

# Initialize API and standard DBs
app = FastAPI(title="Quran AI RAG Bot")
db.init_user_db()

# Ensure at least one dev user exists (Naved)
if not db.get_user("naved"):
    db.create_user("naved", auth.get_password_hash("1234"), "naved@example.com")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Client Setup
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

ai_client = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)

# Auth Dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.get_user(username)
    if user is None or user["disabled"]:
        raise credentials_exception
    return dict(user)

# --- Routes ---

@app.post("/token", response_model=auth.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user(form_data.username)
    if not user or not auth.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

class MessageRequest(BaseModel):
    content: str
    thread_id: int = 1  # Hardcoded default for testing

class ChatResponse(BaseModel):
    author: str
    content: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: MessageRequest, current_user: dict = Depends(get_current_user)):
    user_msg = request.content
    thread_id = request.thread_id

    # 1. Save user message
    db.save_msg(thread_id, "user", user_msg)
    
    # 2. Retrieve context from Quran DB (RAG)
    related_verses = db.search_quran(user_msg)
    
    context_str = ""
    if related_verses:
        context_str = "Use the following verified Quranic verses to inform your answer:\n"
        for v in related_verses:
            context_str += f"- Surah {v['name_en']} Verse {v['ayah_id']}: {v['translation']} (Arabic: {v['arabic_text']})\n"

    # 3. Load chat history
    history = db.load_messages(thread_id)

    # 4. Construct System Prompt
    system_prompt = (
        "You are an AI Quranic Assistant. Your primary goal is to provide accurate information based strictly on the provided context verses. "
        "Always cite the Surah name and Verse number when referencing the text. "
        "If the user's question cannot be answered using the provided context, state that clearly."
    )

    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Context Data:\n{context_str}"}
    ] + history

    # 5. Call Local AI Model via Tunnel
    try:
        response = ai_client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages_payload,
            stream=False
        )
        ai_response = response.choices[0].message.content

        # 6. Save AI response
        db.save_msg(thread_id, "assistant", ai_response)

        return ChatResponse(author="Assistant", content=ai_response)

    except Exception as e:
        print(f"AI Connection Error: {e}")
        raise HTTPException(status_code=503, detail="Local AI Server Unreachable. Ensure Ollama/Tunnel is running.")
