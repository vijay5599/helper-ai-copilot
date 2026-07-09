import os
import json
import asyncio
import time
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from openai import AsyncOpenAI
import websockets
from prompts import get_system_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("HelperAI")

load_dotenv()

app = FastAPI()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client = None
if os.getenv("GROQ_API_KEY"):
    groq_client = AsyncOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        max_retries=0
    )
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.websocket("/ws/copilot")
async def copilot_endpoint(websocket: WebSocket):
    await websocket.accept()
    context_buffer = ""
    logger.info("Client connected to WebSocket")
    # Using nova-2 with domain-specific keywords to heavily boost recognition of tech jargon
    keywords = "&keywords=multithreading:2&keywords=backend:2&keywords=frontend:2&keywords=LLM:2&keywords=RAG:2&keywords=API:2&keywords=React:2&keywords=FastAPI:2&keywords=type%20hints:2&keywords=Pydantic:2&keywords=BaseModel:2&keywords=CORS:2&keywords=Node.js:2&keywords=LoRA:2&keywords=fine-tuning:2&keywords=zero-shot:2&keywords=few-shot:2&keywords=vector%20database:2&keywords=Chain-of-Thought:2&keywords=CORS&keywords=hallucination:2&keywords=Hugging%20Face:2&keywords=semantic%20search:2&keywords=ChromaDB:2&keywords=LangGraph:2&keywords=LangChain:2&keywords=LiteLLM:2&keywords=qTest:2&keywords=NetApp:2&keywords=Graphene:2&keywords=Next.js:2&keywords=Redux:2&keywords=DevOps:2&keywords=CI/CD:2"
    deepgram_url = f"wss://api.deepgram.com/v1/listen?model=nova-2&language=en-IN&smart_format=true&keepalive=true{keywords}"
    try:
        # Using raw websockets instead of the SDK to avoid Python version compatibility issues
        async with websockets.connect(
            deepgram_url, 
            additional_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        ) as dg_ws:
            logger.info("Connected to Deepgram API directly")
            
            async def receiver():
                nonlocal context_buffer
                try:
                    async for dg_message in dg_ws:
                        msg = json.loads(dg_message)
                        if msg.get("type") == "Results":
                            is_final = msg.get("is_final", False)
                            sentence = msg["channel"]["alternatives"][0].get("transcript", "")
                            
                            if sentence and is_final:
                                logger.info(f"Deepgram transcript (final): {sentence}")
                                context_buffer += sentence + " "
                                await websocket.send_text(json.dumps({
                                    "type": "transcript",
                                    "text": context_buffer
                                }))
                            elif sentence:
                                # Send intermediate results without permanently adding to buffer
                                await websocket.send_text(json.dumps({
                                    "type": "transcript",
                                    "text": context_buffer + sentence
                                }))
                        else:
                            logger.info(f"Deepgram message: {msg}")
                except Exception as e:
                    logger.error(f"Deepgram receiver error: {e}")

            # Run Deepgram receiver and keep_alive tasks concurrently
            receiver_task = asyncio.create_task(receiver())

            async def keep_alive():
                try:
                    while True:
                        await asyncio.sleep(5)
                        logger.info("Sending KeepAlive to Deepgram...")
                        await dg_ws.send(json.dumps({"type": "KeepAlive"}))
                except asyncio.CancelledError:
                    pass
                except Exception as ke_err:
                    logger.error(f"Deepgram keep-alive error: {ke_err}")

            keep_alive_task = asyncio.create_task(keep_alive())

            try:
                while True:
                    message = await websocket.receive()

                    if "text" in message:
                        data = json.loads(message["text"])
                        
                        if data.get("type") == "clear_transcript":
                            logger.info("Clearing transcript buffer...")
                            context_buffer = ""
                            continue
                            
                        if data.get("type") == "trigger_llm":
                            logger.info("Trigger received, querying LLM...")
                            resume_ctx = data.get("resume", "")
                            print(len(resume_ctx), "len")
                            # Truncate resume context to max 15000 characters (~3750 tokens) to fit Groq's 12k TPM free tier limit while allowing large resumes
                            if len(resume_ctx) > 15000:
                                logger.info("Truncating massive resume context to prevent API rate limits...")
                                resume_ctx = resume_ctx[:15000] + "...\n[TRUNCATED TO SAVE TOKENS]"
                            print(len(resume_ctx), "newwwwwwwww")
                            job_role = data.get("jobRole", "")
                            image_data = data.get("image", "")

                            if not context_buffer.strip() and not image_data:
                                await websocket.send_text(json.dumps({
                                    "type": "answer_chunk",
                                    "text": "Waiting for enough transcript context or screen image..."
                                }))
                                continue

                            # Single-stage fast generation
                            system_message = get_system_prompt("v6", job_role, resume_ctx)

                            user_content = []
                            if context_buffer.strip():
                                query_text = context_buffer.strip()
                                chat_history = data.get("history", [])
                                if chat_history:
                                    last_q = chat_history[-1].get("question", "")
                                    if last_q:
                                        query_text += f" (Context hint: The user is asking a follow-up about the exact topic of their previous question: '{last_q}')"
                                user_content.append({"type": "text", "text": query_text})
                            else:
                                user_content.append({"type": "text", "text": "No transcript available. Analyze the screen and provide guidance."})

                            if image_data:
                                user_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_data
                                    }
                                })

                            messages = [
                                {"role": "system", "content": system_message}
                            ]

                            chat_history = data.get("history", [])
                            # Keep only the last 2 interactions in memory to save tokens and maintain speed
                            recent_history = chat_history[-2:]
                            for item in recent_history:
                                if item.get("question") and item.get("answer"):
                                    messages.append({"role": "user", "content": item["question"]})
                                    # Truncate previous answers to keep context small and fast
                                    truncated_ans = item["answer"][:300] + "..." if len(item["answer"]) > 300 else item["answer"]
                                    messages.append({"role": "assistant", "content": truncated_ans})

                            messages.append({"role": "user", "content": user_content})

                            start_time = time.time()
                            first_token_time = None
                            
                            # Use Groq if available, unless there's an image (Groq text models don't support image_url perfectly yet)
                            use_groq = os.getenv("USE_GROQ", "true").lower() == "true" and groq_client is not None
                            
                            if use_groq and not image_data:
                                logger.info("🚀 Request sent to Groq (llama-3.1-8b-instant)...")
                                try:
                                    stream = await groq_client.chat.completions.create(
                                        model="llama-3.1-8b-instant",
                                        messages=messages,
                                        stream=True,
                                        max_tokens=1000
                                    )
                                except Exception as e:
                                    logger.warning(f"⚠️ Groq request failed ({e}). Falling back to OpenAI (gpt-4o-mini)...")
                                    stream = await openai_client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=messages,
                                        stream=True,
                                        max_tokens=1000
                                    )
                            else:
                                logger.info(f"🚀 Request sent to OpenAI (gpt-4o-mini)... Image present: {bool(image_data)}")
                                stream = await openai_client.chat.completions.create(
                                    model="gpt-4o-mini",
                                    messages=messages,
                                    stream=True,
                                    max_tokens=1000
                                )
                            
                            full_answer = ""
                            async for chunk in stream:
                                if first_token_time is None:
                                    first_token_time = time.time()
                                    ttft = (first_token_time - start_time) * 1000
                                    logger.info(f"⏱️  Time to First Token (TTFT): {ttft:.0f} ms")

                                content = chunk.choices[0].delta.content
                                if content:
                                    full_answer += content
                                    await websocket.send_text(json.dumps({
                                        "type": "answer_chunk",
                                        "text": full_answer
                                    }))
                            
                            end_time = time.time()
                            total_time = (end_time - start_time) * 1000
                            if first_token_time:
                                generation_time = end_time - first_token_time
                                approx_tokens = len(full_answer) / 4 # ~4 chars per token
                                tps = approx_tokens / generation_time if generation_time > 0 else 0
                                logger.info(f"✅  Total Latency: {total_time:.0f} ms | Speed: {tps:.1f} tokens/sec")
                            
                            context_buffer = ""

                    elif "bytes" in message:
                        await dg_ws.send(message["bytes"])
            finally:
                receiver_task.cancel()
                keep_alive_task.cancel()
                    
    except WebSocketDisconnect:
        logger.info("Client disconnected cleanly")
    except RuntimeError as e:
        if "Cannot call" in str(e):
            logger.info("Client disconnected (RuntimeError)")
        else:
            logger.error(f"RuntimeError: {e}")
    except Exception as e:
        logger.error(f"Exception: {e}")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

