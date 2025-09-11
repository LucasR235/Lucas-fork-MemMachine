# Book Logging and Recommendation System

A high-level book logging and recommendation system built on top of the MemMachine profile backend, using a generic example server with book-specific adapters.

## Overview

This system allows users to:
- Log books with detailed information (title, author, rating, status, additional_info)
- Track reading progress and preferences
- Get personalized book recommendations
- View reading statistics and analytics

## Architecture

The book agent uses a simple, direct architecture:

### Components

1. **Example Server** (`example_server.py`)
   - Generic FastAPI server for memory operations
   - Handles storage and retrieval of memories
   - Provides standard REST API endpoints

2. **Book Query Constructor** (`book_query_constructor.py`)
   - Handles book-specific query formatting
   - Routes different types of book queries (logging, recommendations, analytics)
   - Formats responses for different query types

3. **Book Prompt** (`../memmachine/src/memmachine/profile_memory/prompt/book_prompt.py`)
   - Defines book-specific data extraction rules
   - Handles book profile creation and updates
   - Manages memory consolidation for book data

4. **Frontend** (`book_frontend.py`)
   - Streamlit web application
   - User-friendly interface for book logging
   - Directly integrates with example server and book query constructor
   - Real-time recommendations and analytics

## Data Model

### Book Storage Format
- **Tag**: `bk-{book_name}` (e.g., `bk-Scythe`)
- **Features**: `book_title`, `author`, `rating`, `status`, `additional_info`, `genre`, `start_date`, `finish_date`
- **Values**: Corresponding book information
- **Additional Info**: Unified field containing reviews, notes, quotes, and reading preferences

### User Storage Format
- **Tag**: `user-{user_name}` (e.g., `user-alice`)
- **Features**: `additional_info` (unified field for all user preferences)
- **Values**: User preference information

## Usage

### Quick Start
```bash
# Start both the server and frontend
python start_book_system.py
```

### Manual Start
```bash
# Terminal 1: Start the example server
python example_server.py

# Terminal 2: Start the frontend
streamlit run book_frontend.py
```

### Environment Variables

```bash
# Optional: Set custom ports
export BOOK_SERVER_URL="http://localhost:8000"
export MEMORY_BACKEND_URL="http://localhost:8080"
export EXAMPLE_SERVER_PORT="8000"
```

### API Endpoints

- `POST /memory` - Store book data
- `GET /memory` - Retrieve book data  
- `POST /memory/store-and-search` - Store and search in one operation

## Features

### Book Logging
- **Hard Fields**: Book title, author, rating (1-5), status (to-read, reading, finished, abandoned, on-hold)
- **Unified Field**: Additional Information (reviews, notes, quotes, reading preferences)
- **Derived Fields**: Genre, style, start/finish dates

### Recommendations
- General recommendations based on reading history
- Similar books to previously read titles
- Genre-based recommendations
- Author-based recommendations

### Analytics
- Reading statistics (total books, finished, currently reading)
- Rating distribution
- Genre preferences
- Reading timeline

## Configuration

The system uses environment variables for configuration:

- `BOOK_SERVER_URL`: URL of the book server (default: http://localhost:8001)
- `MEMORY_BACKEND_URL`: URL of the MemMachine backend (default: http://localhost:8080)
- `BOOK_PORT`: Port for the book server (default: 8001)
- Database configuration (same as MemMachine)

## Integration with MemMachine

The book agent integrates with MemMachine's profile memory system:

1. **Profile Memory**: Stores book profiles and user preferences
2. **Episodic Memory**: Stores reading timeline and notes
3. **Memory Consolidation**: Automatically consolidates related book memories

## Example Usage

### Logging a Book
```
Book: Scythe
Author: Neal Shusterman
Rating: 5/5
Status: finished
Genre: Science Fiction
Review: Amazing dystopian world-building
Notes: Great character development, complex themes
```

### Getting Recommendations
```
Query: "Recommend books similar to Scythe"
Response: Foundation series, Dune, The Martian, etc.
```

## Development

The book agent is designed to be easily extensible:

1. **Add new fields**: Update the FEATURES list in `book_prompt.py`
2. **Add new query types**: Extend the ROUTING_RULES in `query_constructor.py`
3. **Add new UI components**: Extend the frontend in `book_frontend.py`
4. **Add new API endpoints**: Extend the server in `book_server.py`

## Testing

The system can be tested by:

1. Starting the MemMachine backend
2. Starting the book server
3. Running the frontend application
4. Logging books and testing recommendations

## Dependencies

- FastAPI (server)
- Streamlit (frontend)
- MemMachine (backend)
- PostgreSQL (database)
- Python 3.8+
