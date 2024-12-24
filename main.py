from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from textblob import TextBlob
import io
import secrets

app = FastAPI()
security = HTTPBasic()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hardcoded credentials - in production, use a secure database
USERS = {
    "admin": "secretpassword123"
}

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify username and password."""
    # Print credentials for debugging (remove in production)
    print(f"Received credentials - Username: {credentials.username}")
    
    is_username_correct = False
    is_password_correct = False
    
    if credentials.username in USERS:
        is_username_correct = True
        is_password_correct = secrets.compare_digest(
            credentials.password.encode("utf8"),
            USERS[credentials.username].encode("utf8")
        )
    
    # Print authentication results for debugging (remove in production)
    print(f"Username correct: {is_username_correct}")
    print(f"Password correct: {is_password_correct}")
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

def analyze_sentiment(text):
    analysis = TextBlob(str(text))
    if analysis.sentiment.polarity > 0:
        return "positive"
    elif analysis.sentiment.polarity < 0:
        return "negative"
    return "neutral"

@app.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    username: str = Depends(verify_credentials)
):
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Check required columns
        if 'text' not in df.columns:
            return {"error": "CSV must contain 'text' column"}
        
        # Analyze sentiment for each text
        df['sentiment'] = df['text'].apply(analyze_sentiment)
        
        # Calculate sentiment distribution
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        
        # Prepare results
        results = {
            'sentiment_distribution': sentiment_counts,
            'detailed_results': df[['text', 'sentiment']].to_dict('records')
        }
        
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)