

from fastapi import FastAPI, HTTPException

from fastapi import FastAPI
app = FastAPI()
import httpx
from pydantic import BaseModel
url = "https://jsonplaceholder.typicode.com/todos"
class Todo(BaseModel):
    userId: int
    title: str
    completed: bool
class Todoforupdate(BaseModel):
    userId: int | None = None
    title: str | None = None
    completed: bool | None = None

class TodoResponse(BaseModel):
    userId: int
    id: int
    title: str
    completed: bool

@app.post("/create_todo/", status_code=201)
async def create_todo_endpoint(todo: Todo):
    new_todo = todo.model_dump()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=new_todo)
            response.raise_for_status()
            return TodoResponse(**response.json())
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_todos/", status_code=200)
async def get_todos_endpoint(userId: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}?userId={userId}")
            response.raise_for_status()
        return [TodoResponse(**todo) for todo in response.json()]
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.delete("/delete_todo/{todo_id}", status_code=204)
async def delete_todo_endpoint(todo_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{url}/{todo_id}")
            response.raise_for_status()
            return
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/update_todo/{todo_id}")
async def update_todo_endpoint(todo_id: int, todo: Todoforupdate):
       update_data = todo.model_dump(exclude_none=True)
       try:
           async with httpx.AsyncClient() as client:
               response = await client.patch(f"{url}/{todo_id}", json=update_data)
               response.raise_for_status()
               return TodoResponse(**response.json())
       except httpx.HTTPStatusError as e:
           raise HTTPException(status_code=502, detail=str(e))
       except httpx.RequestError as e:
           raise HTTPException(status_code=502, detail=str(e))
       
