import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from openai import AsyncOpenAI
import websockets
from prompts import get_system_prompt

load_dotenv()

app = FastAPI()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.websocket("/ws/copilot")
async def copilot_endpoint(websocket: WebSocket):
    await websocket.accept()
    context_buffer = ""
    print("Client connected to WebSocket")
    deepgram_url = "wss://api.deepgram.com/v1/listen?model=nova-2&language=en-IN&smart_format=true&keepalive=true"
    
    try:
        # Using raw websockets instead of the SDK to avoid Python version compatibility issues
        async with websockets.connect(
            deepgram_url, 
            additional_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        ) as dg_ws:
            print("Connected to Deepgram API directly")
            
            async def receiver():
                nonlocal context_buffer
                try:
                    async for dg_message in dg_ws:
                        msg = json.loads(dg_message)
                        if msg.get("type") == "Results":
                            is_final = msg.get("is_final", False)
                            sentence = msg["channel"]["alternatives"][0].get("transcript", "")
                            
                            if sentence and is_final:
                                print(f"Deepgram transcript (final): {sentence}")
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
                            print(f"Deepgram message: {msg}")
                except Exception as e:
                    print(f"Deepgram receiver error: {e}")

            # Run Deepgram receiver concurrently
            asyncio.create_task(receiver())

            while True:
                message = await websocket.receive()

                if "text" in message:
                    data = json.loads(message["text"])
                    
                    if data.get("type") == "clear_transcript":
                        print("Clearing transcript buffer...")
                        context_buffer = ""
                        continue
                        
                    if data.get("type") == "trigger_llm":
                        print("Trigger received, querying LLM...")
                        resume_ctx = data.get("resume", "")
                        job_role = data.get("jobRole", "")
                        image_data = data.get("image", "")

                        if not context_buffer.strip() and not image_data:
                            await websocket.send_text(json.dumps({
                                "type": "answer_chunk",
                                "text": "Waiting for enough transcript context or screen image..."
                            }))
                            continue

                        # Use v3 (the latest structured prompt version)
                        system_message = get_system_prompt("v3", job_role, resume_ctx)

                        user_content = []
                        if context_buffer.strip():
                            user_content.append({"type": "text", "text": f"Current interview transcript:\n{context_buffer}"})
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
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_content}
                        ]

                        stream = await openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=messages,
                            stream=True,
                            max_tokens=1000
                        )
                        
                        full_answer = ""
                        async for chunk in stream:
                            content = chunk.choices[0].delta.content
                            if content:
                                full_answer += content
                                await websocket.send_text(json.dumps({
                                    "type": "answer_chunk",
                                    "text": full_answer
                                }))
                        
                        context_buffer = ""

                elif "bytes" in message:
                    await dg_ws.send(message["bytes"])
                    
    except WebSocketDisconnect:
        print("Client disconnected cleanly")
    except RuntimeError as e:
        if "Cannot call" in str(e):
            print("Client disconnected (RuntimeError)")
        else:
            print(f"RuntimeError: {e}")
    except Exception as e:
        print(f"Exception: {e}")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

