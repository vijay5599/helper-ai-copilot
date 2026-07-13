import os
import json
import asyncio
import time
import logging
import urllib.parse
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
    keyword_list = [
        # Original & Resume Jargon
        "multithreading", "backend", "frontend", "LLM", "RAG", "API", 
        "React", "FastAPI", "type hints", "Pydantic", "BaseModel", "CORS", 
        "Node.js", "LoRA", "fine-tuning", "zero-shot", "few-shot", "vector database", 
        "Chain-of-Thought", "CoT", "hallucination", "Hugging Face", "semantic search", 
        "ChromaDB", "LangGraph", "LangChain", "LiteLLM", "qTest", "NetApp", 
        "Graphene", "Next.js", "Redux", "DevOps", "CI/CD",
        # GenAI Developer Jargon
        "ChatGPT", "Anthropic", "Llama", "Mistral", "Langfuse", "vLLM", 
        "quantization", "chunking", "embeddings", "Prompt Engineering", 
        "ROUGE", "BLEU", "FAISS", "Qdrant", "Pinecone", "Agentic", "CrewAI", "AutoGen",
        # Full Stack Developer Jargon
        "PostgreSQL", "MongoDB", "Redis", "Kafka", "GraphQL", "WebSockets", 
        "Kubernetes", "Tailwind", "Zustand", "Vite", "OAuth", "JWT", 
        "Nginx", "SQLAlchemy", "Prisma", "ORM",
        # Frontend & React Ecosystem
        "Context API", "useEffect", "useState", "useMemo", "useCallback", 
        "Virtual DOM", "React Router", "Next.js App Router", "Server Components", 
        "Client Components", "hydration", "memoization", "lazy loading", 
        "Redux Thunk", "Redux Saga", "Redux Toolkit", "RTK", "React Query", 
        "TanStack", "Material UI", "MUI", "Framer Motion", "Webpack", "Babel",
        # Node.js Ecosystem
        "Event Loop", "libuv", "V8 engine", "Call Stack", "Microtask Queue", 
        "Macrotask Queue", "Worker Threads", "Child Processes", "streams", 
        "EventEmitter", "middleware", "Express", "NestJS", "CommonJS", "ESM",
        # Next.js Ecosystem
        "SSR", "SSG", "ISR", "CSR", "App Router", "Pages Router", 
        "getStaticProps", "getServerSideProps", "Server Actions", 
        "Code Splitting", "Image Optimization",
        # Python & FastAPI Ecosystem
        "FastAPI", "uvicorn", "Pydantic", "SQLAlchemy", "Alembic", 
        "asyncio", "event loop", "FastAPI cors", "response_model",
        # LangChain Ecosystem
        "LangChain Expression Language", "LCEL", "Runnable", "PromptTemplate", 
        "Chroma", "OpenAIEmbeddings", "ColBERT", "Momentum Black", 
        "ChatPromptTemplate", "MessagesPlaceholder", "StrOutputParser",
        # Deployment & DevOps
        "Docker", "docker-compose", "GitHub Actions", "GitLab CI", "Azure DevOps",
        "CI/CD pipeline", "deployment", "automation", "Azure App Service",
        # Databases & Storage
        "PostgreSQL", "MySQL", "Chroma", "OpenSearch", "Supabase",
        "Azure Blob Storage", "Cloud Storage", "data persistence",
        # AI/ML Concepts
        "Retrieval Augmented Generation", "zero-shot prompting", "few-shot prompting",
        "fine-tuning", "parameter-efficient fine-tuning", "PEFT", "LoRA",
        "quantization", "QLoRA", "embeddings", "vector database", "semantic search",
        # Prompt Engineering
        "prompt engineering", "few-shot prompting", "zero-shot prompting",
        "instruction following", "Chain-of-Thought", "CoT", "role-playing",
    ]
    keywords = "".join([f"&keywords={urllib.parse.quote(k)}:2" for k in keyword_list])
    deepgram_url = f"wss://api.deepgram.com/v1/listen?model=nova-2&language=en-IN&smart_format=true{keywords}"
    dg_ws = None
    dg_connected = False

    async def deepgram_runner():
        nonlocal dg_ws, dg_connected, context_buffer
        while True:
            try:
                if not dg_connected:
                    logger.info("Connecting to Deepgram API directly...")
                    dg_ws = await websockets.connect(
                        deepgram_url,
                        extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
                    )
                    dg_connected = True
                    logger.info("Connected to Deepgram API directly")
                    await websocket.send_text(json.dumps({"type": "restart_audio"}))
                
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
                finally:
                    dg_connected = False
                    if dg_ws:
                        try:
                            await dg_ws.close()
                        except Exception:
                            pass
                    logger.info("Deepgram connection cleanup complete.")
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Deepgram connection error: {e}. Reconnecting to Deepgram in 2s...")
                await asyncio.sleep(2)

    async def keep_alive():
        nonlocal dg_ws, dg_connected
        try:
            while True:
                await asyncio.sleep(5)
                if dg_connected and dg_ws:
                    try:
                        logger.info("Sending KeepAlive to Deepgram...")
                        await dg_ws.send(json.dumps({"type": "KeepAlive"}))
                    except asyncio.CancelledError:
                        raise
                    except Exception as ke_err:
                        logger.error(f"Deepgram keep-alive error: {ke_err}")
        except asyncio.CancelledError:
            pass

    runner_task = None
    keep_alive_task = None
    audio_chunks_received = 0

    try:
        # Start the concurrent tasks
        runner_task = asyncio.create_task(deepgram_runner())
        keep_alive_task = asyncio.create_task(keep_alive())

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
                audio_chunks_received += 1
                if audio_chunks_received == 1:
                    logger.info("Received first audio chunk from client!")
                elif audio_chunks_received % 100 == 0:
                    logger.info(f"Received {audio_chunks_received} audio chunks from client.")

                if dg_connected and dg_ws:
                    try:
                        await dg_ws.send(message["bytes"])
                    except Exception as send_err:
                        logger.error(f"Error sending audio to Deepgram: {send_err}")
    except WebSocketDisconnect:
        logger.info("Client disconnected cleanly")
    except RuntimeError as e:
        if "Cannot call" in str(e):
            logger.info("Client disconnected (RuntimeError)")
        else:
            logger.error(f"RuntimeError: {e}")
    except Exception as e:
        logger.error(f"Exception: {e}")
    finally:
        if runner_task:
            runner_task.cancel()
        if keep_alive_task:
            keep_alive_task.cancel()
        if dg_ws:
            try:
                await dg_ws.close()
            except Exception:
                pass
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

