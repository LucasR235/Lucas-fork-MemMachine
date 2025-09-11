import os
import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import sys
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from book_query_constructor import BookQueryConstructor

# Load environment variables from .env file
load_dotenv()

# Configuration
BOOK_SERVER_URL = os.getenv("BOOK_SERVER_URL", "http://localhost:8000")  # Updated to match example_server port
MEMORY_BACKEND_URL = os.getenv("MEMORY_BACKEND_URL", "http://localhost:8080")

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Initialize book query constructor
book_query_constructor = BookQueryConstructor()

# Initialize OpenAI client with validation
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not set. Please set it as an environment variable.")
    print("Example: export OPENAI_API_KEY='your-openai-api-key'")
    openai_client = None
else:
    try:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        openai_client = None

async def call_llm(formatted_query: str) -> str:
    """Call the LLM with the formatted query to get an actual response"""
    if openai_client is None:
        return "Error: OpenAI client not initialized. Please check your API key configuration."
    
    try:
        response = await openai_client.responses.create(
            model=OPENAI_MODEL,
            input=[{"role": "user", "content": formatted_query}],
            max_output_tokens=4096,
            temperature=0.0,
            top_p=1
        )
        return response.output_text
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

def store_book_data(user_id: str, query: str) -> Dict[str, Any]:
    """Store fixed book input fields (book logging)"""
    try:
        response = requests.post(
            f"{BOOK_SERVER_URL}/memory",
            params={"user_id": user_id, "query": query},
            timeout=30
        )
        response.raise_for_status()
        return {"status": "success", "data": response.text}
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Cannot connect to server. Please check if the backend is running."}
    except Exception as e:
        return {"status": "error", "message": f"Error storing book data: {str(e)}"}

def process_ai_query(user_id: str, query: str) -> Dict[str, Any]:
    """Process AI queries with storage + retrieval + AI processing"""
    try:
        # First, store the query
        store_result = store_book_data(user_id, query)
        if store_result["status"] != "success":
            return store_result
        
        # Then search for relevant data using the GET endpoint
        search_response = requests.get(
            f"{BOOK_SERVER_URL}/memory",
            params={"user_id": user_id, "query": query, "timestamp": datetime.now().isoformat()},
            timeout=30
        )
        search_response.raise_for_status()
        
        search_data = search_response.json()
        
        # Extract profile and context from search results
        profile_memory = search_data.get("data", {}).get("profile", [])
        episodic_memory = search_data.get("data", {}).get("context", [])
        
        # Format the data for book query constructor
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
        
        # Use the book query constructor to format the query properly
        formatted_query = book_query_constructor.create_query(
            profile=profile_str,
            context=context_str,
            query=query
        )
        
        # Call the LLM to get an actual response
        try:
            # Run the async LLM call in the event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            ai_response = loop.run_until_complete(call_llm(formatted_query))
            loop.close()
        except Exception as llm_error:
            ai_response = f"Error calling LLM: {str(llm_error)}"
        
        return {
            "status": "success",
            "ai_response": ai_response,
            "response": ai_response,  # For backward compatibility
            "formatted_query": formatted_query,
            "context": context_str,
            "profile": profile_str
        }
        
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "AI request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Cannot connect to AI service. Please check if the backend is running."}
    except Exception as e:
        return {"status": "error", "message": f"Error processing AI query: {str(e)}"}



# Page setup
st.set_page_config(
    page_title="AI Book Assistant",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #2E86AB;
    text-align: center;
    margin-bottom: 2rem;
}

.section-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #A23B72;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

.book-card {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
}

.recommendation-card {
    background-color: #e8f4f8;
    border: 1px solid #bee5eb;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
}

.stats-card {
    background-color: #f0f8ff;
    border: 1px solid #b3d9ff;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
}

.success-message {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 1rem 0;
}

.error-message {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">📚 AI Book Assistant</div>', unsafe_allow_html=True)

# Sidebar for user selection
with st.sidebar:
    st.markdown("### User Settings")
    user_id = st.text_input("Username", value="default_user", help="Enter your username for book tracking")
    
    # Connection status
    st.markdown("### System Status")
    
    # Initialize connection status in session state
    if "connection_status" not in st.session_state:
        st.session_state.connection_status = None
        st.session_state.connection_last_checked = None
    
    # Only test connection if not recently checked (within last 30 seconds)
    import time
    current_time = time.time()
    should_test_connection = (
        st.session_state.connection_status is None or 
        st.session_state.connection_last_checked is None or
        (current_time - st.session_state.connection_last_checked) > 30
    )
    
    if should_test_connection:
        try:
            # Test backend connection using direct server call
            test_result = store_book_data("test", "test connection")
            if test_result["status"] == "success":
                st.session_state.connection_status = "connected"
                st.success("🟢 Backend Connected")
            else:
                st.session_state.connection_status = "warning"
                st.warning("🟡 Backend Response Issue")
        except:
            st.session_state.connection_status = "offline"
            st.error("🔴 Backend Offline")
        
        st.session_state.connection_last_checked = current_time
    else:
        # Use cached status
        if st.session_state.connection_status == "connected":
            st.success("🟢 Backend Connected")
        elif st.session_state.connection_status == "warning":
            st.warning("🟡 Backend Response Issue")
        else:
            st.error("🔴 Backend Offline")
    
    st.markdown("### Quick Actions")
    if st.button("Clear All Data", use_container_width=True):
        st.success("Data cleared! (Note: This only clears the current session. Book data is stored in the backend.)")
    
    st.markdown("### Navigation")
    page = st.selectbox("Choose Page", ["Log Book", "AI Assistant"])

# Initialize session state
if "quick_query" not in st.session_state:
    st.session_state.quick_query = None

# Main content based on selected page
if page == "Log Book":
    st.markdown('<div class="section-header">📖 Log a New Book</div>', unsafe_allow_html=True)
    
    # Hard Fields (separate input fields)
    col1, col2 = st.columns(2)
    
    with col1:
        book_title = st.text_input("Book Title *", placeholder="e.g., Scythe")
        author = st.text_input("Author *", placeholder="e.g., Neal Shusterman")
        rating = st.selectbox("Rating", ["", "1", "2", "3", "4", "5"], index=0)
        status = st.selectbox("Status", ["", "to-read", "reading", "finished", "abandoned", "on-hold"], index=0)
    
    with col2:
        start_date = st.date_input("Start Date", value=None)
        finish_date = st.date_input("Finish Date", value=None)
        st.info("💡 Genre will be automatically detected by AI based on book content")
    
    # Soft Fields (unified textbox for AI extraction)
    st.markdown("### Additional Information")
    st.markdown("Share your thoughts, notes, quotes, reading preferences, or any other book-related information. AI will automatically extract and organize this data.")
    additional_info = st.text_area("Additional Information", placeholder="Share your thoughts about the book, notes, quotes, reading preferences, or any other book-related information...", height=150)
    
    # Submit button
    if st.button("Log Book", type="primary", use_container_width=True):
        if not book_title or not author:
            st.error("Please fill in at least Book Title and Author fields.")
        else:
            # Show progress indicator
            with st.spinner("Logging your book..."):
                # Format the input data
                book_data = {
                    "book_title": book_title,
                    "author": author,
                    "rating": rating,
                    "status": status,
                    "start_date": start_date.strftime("%Y-%m-%d") if start_date else "",
                    "finish_date": finish_date.strftime("%Y-%m-%d") if finish_date else "",
                    "additional_info": additional_info
                }
                
                # Create query string
                query_parts = []
                if book_title:
                    query_parts.append(f"Book: {book_title}")
                if author:
                    query_parts.append(f"Author: {author}")
                if rating:
                    query_parts.append(f"Rating: {rating}/5")
                if status:
                    query_parts.append(f"Status: {status}")
                if start_date:
                    query_parts.append(f"Started: {start_date.strftime('%Y-%m-%d')}")
                if finish_date:
                    query_parts.append(f"Finished: {finish_date.strftime('%Y-%m-%d')}")
                if additional_info:
                    query_parts.append(f"Additional Information: {additional_info}")
                
                query = ". ".join(query_parts) + "."
                
                # Store the data
                result = store_book_data(user_id, query)
                
                if result["status"] == "success":
                    st.markdown('<div class="success-message">✅ Book logged successfully!</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown(f'<div class="error-message">❌ Error: {result["message"]}</div>', unsafe_allow_html=True)
    
    # AI-powered book query section
    st.markdown("---")
    st.markdown("### 🤖 Ask About Your Books")
    st.markdown("Use natural language to ask questions about your reading history, get recommendations, or analyze your reading patterns.")
    
    ai_query = st.text_area("Ask about your books", placeholder="e.g., 'What sci-fi books have I read?', 'Recommend something similar to Dune', 'What's my reading pattern?', 'What should I read next?'", height=100)
    
    if st.button("Ask AI", type="primary"):
        if ai_query:
            with st.spinner("AI is analyzing your reading data..."):
                ai_result = process_ai_query(user_id, ai_query)
            
            if ai_result["status"] == "success":
                st.markdown("### 🤖 AI Response")
                # Display the AI response (prefer ai_response, fallback to response, then formatted_query)
                if "ai_response" in ai_result:
                    st.markdown(ai_result["ai_response"])
                elif "response" in ai_result:
                    st.markdown(ai_result["response"])
                elif "formatted_query" in ai_result:
                    st.markdown(ai_result["formatted_query"])
                else:
                    st.json(ai_result)
                
                # Show context if available
                if "context" in ai_result and st.checkbox("Show AI reasoning"):
                    st.markdown("#### 🔍 AI Analysis")
                    st.text(ai_result["context"])
            else:
                st.error(f"❌ Error: {ai_result.get('message', 'Unknown error')}")
        else:
            st.warning("⚠️ Please enter a question about your books.")


elif page == "AI Assistant":
    st.markdown('<div class="section-header">🤖 AI Book Assistant</div>', unsafe_allow_html=True)
    
    st.markdown("Ask our AI anything about your books, get recommendations, view your reading stats, or analyze your reading patterns.")
    
    # Quick action buttons
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚 My Books", use_container_width=True):
            st.session_state.quick_query = "Show me all my books with their details"
            st.rerun()
    
    with col2:
        if st.button("📊 Reading Stats", use_container_width=True):
            st.session_state.quick_query = "Show me my reading statistics and patterns"
            st.rerun()
    
    with col3:
        if st.button("🎯 Recommendations", use_container_width=True):
            st.session_state.quick_query = "Recommend books based on my reading history"
            st.rerun()
    
    # Additional quick actions
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("⭐ Highly Rated", use_container_width=True):
            st.session_state.quick_query = "Show me my highest rated books"
            st.rerun()
    
    with col5:
        if st.button("🔮 Something New", use_container_width=True):
            st.session_state.quick_query = "Recommend something completely different from what I usually read"
            st.rerun()
    
    with col6:
        if st.button("📈 Reading Progress", use_container_width=True):
            st.session_state.quick_query = "Show me my reading progress and currently reading books"
            st.rerun()
    
    # AI-powered query interface
    if st.session_state.quick_query:
        ai_query = st.text_area(
            "Ask about your books", 
            value=st.session_state.quick_query,
            placeholder="e.g., 'Show me all my sci-fi books', 'What's my average rating?', 'Recommend something similar to Dune', 'Which genres do I read most?'", 
            height=100,
            key="quick_ai_input"
        )
    else:
        ai_query = st.text_area(
            "Ask about your books", 
            placeholder="e.g., 'Show me all my sci-fi books', 'What's my average rating?', 'Recommend something similar to Dune', 'Which genres do I read most?'", 
            height=100,
            key="ai_input"
        )
    
    if st.button("Ask AI", type="primary", use_container_width=True):
        if ai_query:
            with st.spinner("AI is analyzing your reading data..."):
                result = process_ai_query(user_id, ai_query)
            
            if result["status"] == "success":
                st.markdown('<div class="success-message">🤖 AI Response</div>', unsafe_allow_html=True)
                
                # Display the AI response
                if "ai_response" in result:
                    st.markdown("### 🤖 AI Response")
                    st.markdown(result["ai_response"])
                elif "response" in result:
                    st.markdown("### 🤖 AI Response")
                    st.markdown(result["response"])
                elif "formatted_query" in result:
                    st.markdown("### 🤖 AI Response")
                    st.markdown(result["formatted_query"])
                else:
                    st.json(result)
                
                # Show context if available
                if "context" in result and st.checkbox("Show AI reasoning"):
                    st.markdown("#### 🔍 AI Analysis")
                    st.text(result["context"])
                
                # Clear the quick query after successful response
                if st.session_state.quick_query:
                    st.session_state.quick_query = None
            else:
                st.markdown(f'<div class="error-message">❌ Error: {result.get("message", "Unknown error")}</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please enter a question about your books.")


# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit, MemMachine, and AI")
