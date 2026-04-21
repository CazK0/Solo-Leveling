from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import player  # Make sure your router folder/file is named exactly this

app = FastAPI()

# 1. THE GATEKEEPER (CORS) - Keeps Vercel from being blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. THE HEARTBEAT - Tells the frontend "I am alive!"
@app.get("/")
def home():
    return {"status": "System Online", "message": "Solo Leveling Engine Active"}

# 3. THE LINK - This connects your actual game logic back to the app
# If this line is missing, the /docs page will be empty!
app.include_router(player.router)

# Note: If you have a shadow.py router too, add it here:
# app.include_router(shadow.router)