import os
import requests
import openai
from datetime import datetime
from fastapi import FastAPI, Query
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from book_query_constructor import BookQueryConstructor

load_dotenv()

MEMORY_BACKEND_URL = os.getenv("MEMORY_BACKEND_URL", "http://localhost:8080")
BOOK_PORT = int(os.getenv("BOOK_PORT", "8001"))

app = FastAPI(title="Book Server", description="Book logging and recommendation middleware")

query_constructor = BookQueryConstructor()

async def is_book_message_processed(book_message_id: str, user_id: str, session_id: str) -> bool:
    """Check if book message was already processed by querying MemMachine history"""
    try:
        # Use MemMachine to check if message was already processed
        session_data = {
            "group_id": user_id,
            "agent_id": ["assistant"],
            "user_id": [user_id],
            "session_id": session_id
        }
        
        search_data = {
            "session": session_data,
            "query": f"book_message_id {book_message_id}",  # Search for the specific message ID
            "limit": 5,
            "filter": {"producer_id": user_id}
        }
        
        response = requests.post(f"{MEMORY_BACKEND_URL}/v1/memories/search", json=search_data, timeout=10)
        response.raise_for_status()
        
        search_results = response.json()
        episodic_memory = search_results.get("content", {}).get("episodic_memory", [])
        
        # Check if any memory contains the book_message_id
        for memory in episodic_memory:
            if isinstance(memory, dict) and 'metadata' in memory:
                metadata = memory['metadata']
                if isinstance(metadata, dict) and metadata.get('book_message_id') == book_message_id:
                    print(f"[BOOK] Found duplicate book_message_id in MemMachine: {book_message_id}")
                    return True
        
        return False
    except Exception as e:
        print(f"MemMachine check error: {e}")
        return False

# Removed specific book details and reading stats functions
# These are now handled through MemMachine semantic search + LLM responses

async def generate_openai_response(formatted_query: str, original_query: str) -> str:
    """Generate response using OpenAI chat completion"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY not found in environment")
            return "⚠️ OpenAI API key not configured"
        
        client = openai.AsyncOpenAI(api_key=api_key)
        
        messages = [
            {
                "role": "system", 
                "content": """You are an expert book recommendation assistant with deep knowledge of literature across all genres. Your role is to:

1. Analyze the user's reading history and preferences
2. Provide personalized book recommendations based on their tastes
3. Answer questions about their reading patterns and preferences
4. Suggest books that match their interests, reading level, and mood
5. Explain why you're recommending specific books
6. Consider factors like genre preferences, author styles, themes, and reading complexity

When making recommendations:
- Always explain WHY you're recommending each book
- Consider the user's reading history and preferences
- Suggest a mix of well-known classics and hidden gems
- Mention specific aspects that match their interests
- Be enthusiastic but honest about book quality
- Format recommendations clearly with book title, author, and reasoning

Be conversational, helpful, and insightful in your responses."""
            },
            {
                "role": "user",
                "content": formatted_query
            }
        ]
        
        print(f"[OPENAI] Sending request with {len(formatted_query)} characters")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        print(f"[OPENAI] Generated response: {ai_response[:100]}...")
        return ai_response
        
    except Exception as e:
        print(f"[OPENAI] Error generating response: {e}")
        return f"⚠️ Error generating AI response: {str(e)}"


@app.post("/memory")
async def store_data(user_id: str, query: str, book_message_id: str|None):
    try:
        if book_message_id and await is_book_message_processed(book_message_id, user_id, f"session_{user_id}"):
            print(f"[BOOK] Book message {book_message_id} already processed, skipping")
            return {"status": "skipped", "message": "Message already processed"}
        
        session_data = {
            "group_id": user_id,
            "agent_id": ["assistant"],
            "user_id": [user_id],
            "session_id": f"session_{user_id}"
        }
        episode_data = {
            "session": session_data,
            "producer": user_id,
            "produced_for": "assistant",
            "episode_content": query,
            "episode_type": "message",
            "metadata": {
                "speaker": user_id,
                "timestamp": datetime.now().isoformat(),
                "type": "message",
                "book_message_id": book_message_id
            },
        }
        
        response = requests.post(f"{MEMORY_BACKEND_URL}/v1/memories", json=episode_data, timeout=1000)
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Removed specific book details and reading stats endpoints
# These are now handled through the unified AI query endpoint with MemMachine search

@app.post("/ai-query")
async def process_ai_query(user_id: str, query: str):
    """Process AI queries for semantic search and reasoning about books using MemMachine"""
    try:
        # Use MemMachine's semantic search to get relevant book data
        session_data = {
            "group_id": user_id,
            "agent_id": ["assistant"],
            "user_id": [user_id],
            "session_id": f"session_{user_id}"
        }
        
        # Search for relevant book data based on the query
        search_data = {
            "session": session_data,
            "query": query,  # Use the actual query for semantic search
            "limit": 20,  # Get relevant results
            "filter": {"producer_id": user_id}
        }
        
        response = requests.post(f"{MEMORY_BACKEND_URL}/v1/memories/search", json=search_data, timeout=30)
        response.raise_for_status()
        
        search_results = response.json()
        episodic_memory = search_results.get("content", {}).get("episodic_memory", [])
        profile_memory = search_results.get("content", {}).get("profile_memory", [])
        
        # Format the context from MemMachine results
        profile_str = ""
        if profile_memory:
            if isinstance(profile_memory, list):
                profile_str = "\n".join([str(p) for p in profile_memory])
            else:
                profile_str = str(profile_memory)
        
        context_str = ""
        if episodic_memory:
            if isinstance(episodic_memory, list):
                context_str = "\n".join([str(c) for c in episodic_memory])
            else:
                context_str = str(episodic_memory)
        
        # Use the query constructor to format the query properly
        formatted_query = query_constructor.create_query(
            profile=profile_str,
            context=context_str,
            query=query
        )
        
        # Generate AI response using OpenAI
        ai_response = await generate_openai_response(formatted_query, query)
        
        return {
            "status": "success",
            "ai_response": ai_response,
            "response": ai_response,  # For backward compatibility
            "context": context_str,
            "formatted_query": formatted_query,
            "query": query
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/memory")
async def get_data(query: str, user_id: str, timestamp: str):
    try:
        session_data = {
            "group_id": user_id,
            "agent_id": ["assistant"],
            "user_id": [user_id],
            "session_id": f"session_{user_id}"
        }
        search_data = {
            "session": session_data,
            "query": query,
            "limit": 20,
            "filter": {"producer_id": user_id}
        }
        
        response = requests.post(f"{MEMORY_BACKEND_URL}/v1/memories/search", json=search_data, timeout=1000)
        
        if response.status_code != 200:
            return {"status": "error", "message": f"Backend returned {response.status_code}: {response.text}"}

        response_data = response.json()
        
        content = response_data.get("content", {})
        episodic_memory = content.get("episodic_memory", [])
        profile_memory = content.get("profile_memory", [])
        
        profile_str = ""
        if profile_memory:
            if isinstance(profile_memory, list):
                profile_str = "\n".join([str(p) for p in profile_memory])
            else:
                profile_str = str(profile_memory)
        
        context_str = ""
        if episodic_memory:
            if isinstance(episodic_memory, list):
                context_str = "\n".join([str(c) for c in episodic_memory])
            else:
                context_str = str(episodic_memory)
        
        formatted_query = query_constructor.create_query(
            profile=profile_str,
            context=context_str,
            query=query
        )
        
        # Generate AI response using the formatted query
        ai_response = await generate_openai_response(formatted_query, query)
        
        return {
            "status": "success", 
            "data": {
                "profile": profile_memory,
                "context": episodic_memory
            },
            "formatted_query": formatted_query,
            "ai_response": ai_response,
            "query_type": "book"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/memory/store-and-search")
async def store_and_search_data(user_id: str, query: str):
    try:
        session_data = {
            "group_id": user_id,
            "agent_id": ["assistant"],
            "user_id": [user_id],
            "session_id": f"session_{user_id}"
        }
        episode_data = {
            "session": session_data,
            "producer": user_id,
            "produced_for": "assistant",
            "episode_content": query,
            "episode_type": "message",
            "metadata": {
                "speaker": user_id,
                "timestamp": datetime.now().isoformat(),
                "type": "message"
            },
        }
        
        resp = requests.post(f"{MEMORY_BACKEND_URL}/v1/memories", json=episode_data, timeout=1000)
        
        if resp.status_code != 200:
            return {"status": "error", "message": f"Store failed with {resp.status_code}: {resp.text}"}
        
        search_data = {
            "session": session_data,
            "query": query,
            "limit": 5,
            "filter": {"producer_id": user_id}
        }
        
        search_resp = requests.post(f"{MEMORY_BACKEND_URL}/v1/memories/search", json=search_data, timeout=1000)
        
        if search_resp.status_code != 200:
            return {"status": "error", "message": f"Search failed with {search_resp.status_code}: {search_resp.text}"}
        
        search_resp.raise_for_status()
        
        search_results = search_resp.json()
        
        content = search_results.get("content", {})
        episodic_memory = content.get("episodic_memory", [])
        profile_memory = content.get("profile_memory", [])
        
        profile_str = ""
        if profile_memory:
            if isinstance(profile_memory, list):
                profile_str = "\n".join([str(p) for p in profile_memory])
            else:
                profile_str = str(profile_memory)
        
        context_str = ""
        if episodic_memory:
            if isinstance(episodic_memory, list):
                context_str = "\n".join([str(c) for c in episodic_memory])
            else:
                context_str = str(episodic_memory)
        
        formatted_response = query_constructor.create_query(
            profile=profile_str,
            context=context_str,
            query=query
        )
        
        if profile_memory and episodic_memory:
            return f"Profile: {profile_memory}\n\nContext: {episodic_memory}\n\nFormatted Response:\n{formatted_response}"
        elif profile_memory:
            return f"Profile: {profile_memory}\n\nFormatted Response:\n{formatted_response}"
        elif episodic_memory:
            return f"Context: {episodic_memory}\n\nFormatted Response:\n{formatted_response}"
        else:
            return f"Message ingested successfully. No relevant context found yet.\n\nFormatted Response:\n{formatted_response}"
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Database connection pool no longer needed - using MemMachine API instead

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BOOK_PORT)
