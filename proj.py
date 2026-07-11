from urllib import response

from fastapi import FastAPI, HTTPException
app = FastAPI()

from pydantic import BaseModel
import httpx
import pinecone
from typing import List
from tenacity import retry, wait_random_exponential, stop_after_attempt


import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
PORT = int(os.getenv("PORT", 5000))

# --- clients ---
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))




app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class ChatMessage(BaseModel):
    role: str
    content: str

class user_question_type(BaseModel):
    question: str
    namespace: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str   





def embed_texts(texts: List[str], input_type: str = "passage") -> List[List[float]]:
    """Embed a list of strings using Pinecone's hosted inference API."""
    result = pc.inference.embed(
        model=EMBED_MODEL,
        inputs=texts,
        parameters={"input_type": input_type, "truncate": "END"},
    )
    return [r["values"] for r in result]




@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def call_groq(messages, temperature=0.2, max_tokens=1000):
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


@app.post("/chat/", status_code=200)
def chat(user_question: user_question_type):
    try:
        

        query_vector=embed_texts([user_question.question], input_type="query")[0]
            
        results = index.query(
            vector=query_vector,
            namespace=user_question.namespace,
            top_k=4,
            include_metadata=True,
            )
            

        matches = [r for r in results["matches"] if r["score"] > 0.45]
        if len(matches) == 0:
             matches = results["matches"][:2]

        context = "\n\n---\n\n".join([r["metadata"]["text"] for r in matches])

        system_prompt = (
            "You are a helpful assistant that answers questions based on the provided document context.\n\n"
            "Rules:\n"
            "- Quote the relevant sentence directly from the context\n"
            "- Then explain it in simple terms\n"
            "- If the user talks with you generally like greeting, answer also with a greeting and say what you can help them with today\n"
            "- If the answer is NOT in the context, say ONLY: 'This is not covered in the provided document'\n"
            "- Never answer from your own knowledge, only from the context\n"
            "- If multiple parts are relevant, mention ALL of them\n"
            "- If a question has multiple scenarios, explain each one separately\n\n"
            f"Context:\n{context}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        for h in user_question.history:
            messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": user_question.query})

        full_prompt = " ".join([m["content"] for m in messages])
        num_tokens = len(encoding.encode(full_prompt))

        if num_tokens > 6000:
            return ChatResponse(response="Your message and history are too long, please start a new conversation.")

        response = call_groq(messages)
        response.raise_for_status()
        return ChatResponse(response=response.choices[0].message.content)
       
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class file_type(BaseModel):
    namespace: str
    file_url: str

class ProcessResponse(BaseModel):
    status: str
    chunks: int


@app.post("/save-pinecone-namespace/",response_model=ProcessResponse, status_code=201)
async def save_pinecone_namespace(req:file_type):


    
        

        try:
            async with httpx.AsyncClient() as client:

                print("Starting processing for namespace:", req.namespace)

                resp = await client.get(req.file_url)
                resp.raise_for_status()
                print("PDF downloaded")

                reader = PdfReader(BytesIO(resp.content))
                full_text = ""
                for page in reader.pages:
                    full_text += (page.extract_text() or "") + "\n"
                print("Text extracted, length:", len(full_text))

                chunks = chunk_text(full_text)
                print("Chunks created:", len(chunks))

                # Pinecone inference API caps batch size; chunk into groups of 96
                embeddings = []
                batch_size = 96
                for start in range(0, len(chunks), batch_size):
                    batch = chunks[start:start + batch_size]
                    embeddings.extend(embed_texts(batch, input_type="passage"))
                print("Embeddings done")

                vectors = [
                    {"id": f"{req.namespace}-{i}", "values": embeddings[i], "metadata": {"text": chunks[i]}}
                    for i in range(len(chunks))
                ]
                index.upsert(vectors=vectors, namespace=req.namespace)
                print("Upserted to Pinecone")

                NODE_URL = os.getenv("NODE_SERVICE_URL", f"http://localhost:{PORT}")

                callback = await client.post(f"{NODE_URL}/api/documents/status",
                    json={"namespace": req.namespace, "status": "ready"})
                print("Callback status:", callback.status_code)

                return ProcessResponse(status="done", chunks=len(chunks))



            
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=str(e))
        
@app.delete("/delete-pinecone-namespace/{namespace}", status_code=204)
async def delete_pinecone_namespace(namespace: str):
    try:
        index.delete(delete_all=True, namespace=namespace)
        return {"status": "deleted"}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))
    



class complete_request(BaseModel):
    namespace: str
    status: str

@app.post("/complete/", status_code=200)
async def complete(req: complete_request):
    return {"namespace": req.namespace, "status": req.status}



@app.get("/generate_quiz/", status_code=200)
def generate_quiz(namespace:str):
    try:
        
        query_vector=embed_texts(["generate a quiz"], input_type="query")[0]
            
        results = index.query(
            vector=query_vector,
            namespace=namespace,
            top_k=8,
            include_metadata=True,
            )
            

        matches = [r for r in results["matches"] if r["score"] > 0.45]
        if len(matches) == 0:
             matches = results["matches"][:2]

        context = "\n\n---\n\n".join([r["metadata"]["text"] for r in matches])

        system_prompt = (
            "You are a helpful assistant that generates quizzes based on the provided document context.\n\n"
            "Rules:\n"
            "- Generate a quiz with 5 questions based on the context\n"
            "- Each question should have 4 multiple-choice options\n"
            "- Provide the correct answer for each question\n"
            "- If the answer is NOT in the context, say ONLY: 'This is not covered in the provided document'\n\n"
            f"Context:\n{context}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": req.question})

        full_prompt = " ".join([m["content"] for m in messages])
        num_tokens = len(encoding.encode(full_prompt))

        if num_tokens > 6000:
            return {"error": "Your message and history are too long, please start a new conversation."}
        


        response = call_groq(
        messages=[{"role": "user", "content": system_prompt}],
        temperature=0.7,
        max_tokens=1500
    )

        raw = response.choices[0].message.content.strip()
        questions = json.loads(raw)

        return {"questions": questions}
       
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))
        



        
        


