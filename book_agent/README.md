# Book Logging and Recommendation System

A high-level book logging and recommendation system built on top of the MemMachine profile backend, following the same architecture as the CRM agent.

## Overview

This system allows users to:
- Log books with detailed information (title, author, rating, status, review, notes)
- Track reading progress and preferences
- Get personalized book recommendations
- View reading statistics and analytics

## Architecture

The book agent follows the same high-level pattern as the CRM agent:

### Components

1. **Query Constructor** (`query_constructor.py`)
   - Handles book-specific query formatting
   - Routes different types of book queries (logging, recommendations, analytics)
   - Formats responses for different query types

2. **Prompt System** (`../memmachine/src/memmachine/profile_memory/prompt/book_prompt.py`)
   - Defines book-specific data extraction rules
   - Handles book profile creation and updates
   - Manages memory consolidation for book data

3. **Server** (`book_server.py`)
   - FastAPI server for handling book operations
   - Integrates with MemMachine backend
   - Provides REST API endpoints for book data

4. **Frontend** (`book_frontend.py`)
   - Streamlit web application
   - User-friendly interface for book logging
   - Real-time recommendations and analytics

## Data Model

### Book Storage Format
- **Tag**: `bk-{book_name}` (e.g., `bk-Scythe`)
- **Features**: `book_title`, `author`, `rating`, `status`, `review`, `notes`, `genre`, `style`, `start_date`, `finish_date`
- **Values**: Corresponding book information

### User Storage Format
- **Tag**: `user-{user_name}` (e.g., `user-alice`)
- **Features**: `reading_preferences`, `user_preferences`
- **Values**: User preference information

## Usage

### Starting the Book Server

```bash
cd agents/book
python book_server.py
```

The server will run on port 8001 by default.

### Running the Frontend

```bash
cd agents/book
streamlit run book_frontend.py
```

### API Endpoints

- `POST /memory` - Store book data
- `GET /memory` - Retrieve book data
- `POST /memory/store-and-search` - Store and search in one operation

## Features

### Book Logging
- **Hard Fields**: Book title, author, rating (1-5), status (to-read, reading, finished, abandoned, on-hold)
- **Soft Fields**: Review, notes, reading preferences
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
