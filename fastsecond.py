from fastapi import FastAPI, HTTPException  


app = FastAPI()
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
url = "https://example.com/some/long/path"
import random
import string
import datetime
import requests
class ShortenResponse(BaseModel):
    original_url: str
    short_code: str
    created_at: str
    nb_clicks: int

class classurl(BaseModel):
    url: str


db = {
    "xpKhvM": {
        "original_url": "https://example.com/some/long/path",
        "short_code": "xpKhvM",
        "created_at": "2026-07-09 11:02:28",
        "nb_clicks": 3
    },
    "aB9k2Q": {
        "original_url": "https://www.wikipedia.org",
        "short_code": "aB9k2Q",
        "created_at": "2026-07-09 11:15:44",
        "nb_clicks": 0
    }
}

def function_that_generates_short_code(url: str) -> str:
    #make code randomly generated
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return code

def function_that_returns_current_timestamp() -> str:
    #make timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

def function_that_returns_number_of_clicks(url: str) -> int:
    # Implement your logic to return the number of clicks for the given URL
    return 0  # Example number of clicks

@app.post("/shorten/", status_code=201)
def shorten_url(url: classurl):
    try:
        
            res={}

            res["original_url"]=url.url
            res["short_code"]=function_that_generates_short_code(url.url)
            res["created_at"]=function_that_returns_current_timestamp()
            res["nb_clicks"]=function_that_returns_number_of_clicks(url.url)
            db[res["short_code"]]=res
            return ShortenResponse(**res)



    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/get_shortened_url/{short_code}", status_code=200)
def get_shortened_url(short_code: str):
    try:
        if short_code in db:
            db[short_code]["nb_clicks"] += 1  # Increment the number of clicks

            return ShortenResponse(**db[short_code])
        else:
            raise HTTPException(status_code=404, detail="Short code not found")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_title/", status_code=200)
async def get_title(url: str):

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            page_title = soup.title.string.strip() if soup.title and soup.title.string else None
            
            return {"title": page_title}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))