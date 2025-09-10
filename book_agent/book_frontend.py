import os
import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

# Configuration
BOOK_SERVER_URL = os.getenv("BOOK_SERVER_URL", "http://localhost:8001")
MEMORY_BACKEND_URL = os.getenv("MEMORY_BACKEND_URL", "http://localhost:8080")

def store_book_data(user_id: str, query: str) -> Dict[str, Any]:
    """Store book data in the memory backend"""
    try:
        response = requests.post(
            f"{BOOK_SERVER_URL}/memory/store-and-search",
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

def get_book_data(user_id: str, query: str) -> Dict[str, Any]:
    """Get book data from the memory backend"""
    try:
        response = requests.get(
            f"{BOOK_SERVER_URL}/memory",
            params={"user_id": user_id, "query": query, "timestamp": datetime.now().isoformat()},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Cannot connect to server. Please check if the backend is running."}
    except Exception as e:
        return {"status": "error", "message": f"Error retrieving book data: {str(e)}"}


def get_ai_book_query(user_id: str, query: str) -> Dict[str, Any]:
    """Get AI-powered book query results for semantic search and reasoning"""
    try:
        response = requests.post(
            f"{BOOK_SERVER_URL}/ai-query",
            params={"user_id": user_id, "query": query},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
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
    try:
        # Test backend connection using AI query endpoint
        response = requests.post(f"{BOOK_SERVER_URL}/ai-query", params={"user_id": "test", "query": "test connection"}, timeout=5)
        if response.status_code == 200:
            st.success("🟢 Backend Connected")
        else:
            st.warning("🟡 Backend Response Issue")
    except:
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
    
    # Soft Fields (single textbox)
    st.markdown("### Additional Information")
    review = st.text_area("Review", placeholder="Share your thoughts about the book...", height=100)
    notes = st.text_area("Notes", placeholder="Any specific notes, quotes, or observations...", height=100)
    preferences = st.text_area("Reading Preferences", placeholder="What genres/authors do you like or dislike?", height=80)
    
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
                    "review": review,
                    "notes": notes,
                    "preferences": preferences
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
                if review:
                    query_parts.append(f"Review: {review}")
                if notes:
                    query_parts.append(f"Notes: {notes}")
                if preferences:
                    query_parts.append(f"Preferences: {preferences}")
                
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
                ai_result = get_ai_book_query(user_id, ai_query)
            
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
                result = get_ai_book_query(user_id, ai_query)
            
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
