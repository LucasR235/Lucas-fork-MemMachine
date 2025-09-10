"""
Book Query Constructor for agent query prompt for Intelligent Memory System
Optimized for book logging and recommendation system
"""
from typing import Optional, Dict, Any, Union
import logging, sys, os, json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .base_query_constructor import BaseQueryConstructor

logger = logging.getLogger(__name__)

# -----------------------
# QUICK ACCESS TO MAIN CONFIG
# -----------------------
# 🔗 MAIN CONFIG: Jump to line ~260 (search for "All Configuration Consolidation")
# The CONFIG dictionary contains all prompt configuration and is the main entry point
# for modifying the Book query constructor behavior.

# -----------------------
# Helper formatters
# -----------------------
def _current_date_iso() -> str:
    """Get current date in ISO format"""
    return datetime.now().strftime("%Y-%m-%d")

# -----------------------
# SYSTEM PROMPT CONFIG
# -----------------------
SYSTEM_PROMPT = '''
You are an expert book assistant specializing in reading analysis and recommendations. 
Provide accurate, helpful responses based on the user's reading data and preferences.
'''

# -----------------------
# ROUTING CONFIGURATIONS
# -----------------------
ROUTING_RULES = '''
Query Type Detection and Response Routing:

• **Book Logging Queries** (use book logging format):
  - "I just finished reading Scythe by Neal Shusterman", "Started reading Dune today"
  - "Rate this book 4/5", "Mark this as finished", "Add notes about the ending"
  - "Log book: [book name] by [author]", "Update my reading status"
  - Book input requests: title, author, rating, status, review, notes
  - **Frontend Structured Input**: "Book: [title] | Author: [author] | Rating: [rating]/5 | Status: [status] | Review: [review] | Notes: [notes] | Preferences: [preferences]"
  - **IMPORTANT**: Always derive genre from book content, title, or author context

• **Book Profile Queries** (use Book Output Template):
  - "show me my Scythe data", "tell me about Dune", "what's my status on Foundation"
  - "book details for [book name]", "full info on [book name]", "complete book profile"
  - Requests for comprehensive book information (multiple fields or general overview)

• **Recommendation Queries** (use recommendation format):
  - "recommend me a book", "what should I read next", "suggest something similar to Dune"
  - "find books by Neal Shusterman", "show me sci-fi books", "recommend fantasy"
  - "books like [book name]", "similar to [author]", "recommend by genre"
  - **CRITICAL**: Always check reading history to avoid recommending already read books
  - Cross-reference book titles and authors from context to prevent duplicates

• **Reading Analytics Queries** (use analytics format):
  - "how many books have I read", "what's my reading progress", "show me my stats"
  - "which genres do I read most", "what's my average rating", "reading timeline"
  - "books I rated highly", "recently finished books", "currently reading"

• **Search & Filter Queries** (use search format):
  - "find books with rating 5", "show me sci-fi books", "books by specific author"
  - "books I'm currently reading", "finished books this year", "highly rated books"
  - "search for [keyword]", "filter by [criteria]", "books matching [pattern]"

• **User Preference Queries** (use preference format):
  - "what genres do I like", "who are my favorite authors", "what's my reading style"
  - "update my preferences", "I like fantasy now", "add author to favorites"
  - "remove genre from dislikes", "update reading preferences"

• **General Book Queries** (use appropriate format based on content):
  - "help me organize my reading", "what should I focus on reading"
  - "show me my reading list", "what books need attention"

CRITICAL DECISION TREE:
1. If query asks for book LOGGING (adding/updating book data) → Use BOOK_LOGGING_RULES
2. If query asks for book PROFILE information for a SINGLE book → Use BOOK_OUTPUT_TEMPLATE
3. If query asks for RECOMMENDATIONS → Use RECOMMENDATION_FORMAT
4. If query asks for READING ANALYTICS → Use analytics format
5. If query asks for SEARCH/FILTER results → Use search format
6. If query asks for USER PREFERENCES → Use preference format
7. All other queries → Use appropriate format based on content

NEVER use the full Book Output Template for logging requests or multi-book queries.
• **For all other queries**: Answer with the data given to the best of your ability while following the general output rules and formatting requirements.
'''

# -----------------------
# DATE HANDLING CONFIG
# -----------------------
DATE_HANDLING_RULES = '''
*Date Handling Rules:*
• Use EDTF format for incomplete dates, ISO format for complete dates
• M/D format (e.g., "7/28:", "5/19:") → output as "[--MM-DD] content" format
• Complete dates (YYYY-MM-DD) → output as "[YYYY-MM-DD] content" format
• Parse consistently across ALL fields - start_date, finish_date, notes
• *Examples*: "7/28: content" → "[--07-28] content", "5/19: content" → "[--05-19] content"
• *Wrong*: 7/28: → [2025-07-28] | *Correct*: 7/28: → [--07-28]
• Complete dates use ISO format (YYYY-MM-DD), incomplete dates use EDTF format
• Multiple dates in sequence: split into separate timeline entries
• For timeline entries: include date in both value string and date field as "[EDTF_date] content"
• Error handling: If date does not exist at all or parsing fails completely, set date to <CURRENT_DATE>.
• Only include all entries if the user explicitly requests it.
'''

# -----------------------
# +N MORE RULES CONFIG
# -----------------------
PLUS_N_MORE_RULES = '''
*+N More Rules (Apply to ALL sections):*
• +N more MUST be on its own separate line below the last entry. Never inline with anything else.
• +N more MUST have a blank line above it and be completely separate from all other content
• Format as: "+N more" (not <+N>)
• NEVER show "+0 more" - if N = 0, show NOTHING.
• There must be a completely empty line between the last entry and +N more

*Examples of CORRECT +N more formatting:*
CORRECT:
[--05-19] Great character development
[--05-17] Plot twist was unexpected
[--05-12] Started reading today
[--05-05] Highly recommend this book

+2 more

WRONG:
[--05-19] Great character development
[--05-17] Plot twist was unexpected
[--05-12] Started reading today
[--05-05] Highly recommend this book +2 more

WRONG:
[--05-19] Great character development
[--05-17] Plot twist was unexpected
[--05-12] Started reading today
[--05-05] Highly recommend this book
+ 0 more
'''

# -----------------------
# DATA RULES CONFIG
# -----------------------
DATA_EXTRACTION_RULES = '''
Data rules
• Do not invent values. If a requested field is missing, write exactly: (na)
• Carefully parse all the data provided to you in the DATA block including lower scores.
• If the user requests a specific book name, ignore data with tag different from the book name.
• Conflict policy: prefer PROFILE over BOOK_DATA. Prefer newer dated values. If the answer would change due to a conflict, add one line: "Data conflict noted (brief reason)". Do not include this line if there is no conflict.
• Normalize: dates → follow Date Handling Rules above; names → Title Case; merge books case-insensitively; deduplicate authors.
• Values: keep 0 as is. If important unit is unknown, write the number and add "(unit unknown)". If it is provided, make sure to include it.
• Prioritize newer dates and more relevant fields.
'''

# -----------------------
# FIELD CONFIGURATIONS
# -----------------------
AVAILABLE_FIELDS = [
    "book_title", "author", "rating", "status", "review", "notes", 
    "genre", "style", "start_date", "finish_date", "reading_preferences",
    "user_preferences", "recommendation_reason"
]

CANONICAL_FIELDS = [
    "book_title", "author", "rating", "status", "review", "notes",
    "genre", "start_date", "finish_date", "reading_preferences"
]

FIELD_ALIASES = {
    "book_title": "book_title",
    "title": "book_title",
    "author": "author",
    "rating|score|stars": "rating",
    "status|reading_status": "status",
    "review|thoughts|opinion": "review",
    "notes|comments": "notes",
    "genre|category": "genre",
    "style|writing_style": "style",
    "start_date|started": "start_date",
    "finish_date|finished|completed": "finish_date",
    "preferences|user_preferences": "reading_preferences"
}

MULTIPLICITY_RULES = '''
Multiplicity rules
• authors: format as "Author Name" or "Author Name, Co-Author Name" for multiple authors. List up to 3, then "+N more".
• notes: single value timeline field with date (delete-then-add pattern, timeline format). 
• multivalue timeline fields: (review / notes) limit to 4 bullets for review, 3 bullets for notes, then "+N more" unless user requests more.
• genres: list up to 5 genres before "+N more" unless user requests more.
• user_preferences: list up to 6 preferences before "+N more" unless user requests more.
• general lists: for most other multi-item responses, list up to 6 items before "+N more" unless user requests more.
'''

CLARIFICATION_RULES = '''
Clarification
• Ask at most 2 concise questions only if missing info would materially change the answer.
• If a partial answer is possible, answer and add one line starting with: Needs: <missing item>.
• Assumptions may guide formatting only. Label assumptions.
'''

# -----------------------
# GENERAL OUTPUT RULES
# -----------------------
GENERAL_OUTPUT_RULES = '''
Core Formatting Requirements:
• Use ONLY Slack-compatible mrkdwn formatting. NEVER use regular markdown.
• Use *single asterisks* for bold text. NEVER use **double asterisks**
• NEVER use #, ##, ###, ####, etc. headers in your response
• NEVER use markdown links [text](url) - just show the URL or text
• NEVER use markdown lists with numbers or dashes - use • bullet points only
• Be concise but comprehensive - aim for clarity over brevity
• When data is missing, use exactly "(na)" - never invent values
• For multiple items, use bullet points with • symbol
• Always follow the Date Handling Rules for any date formatting
• If conflicting data exists, note it briefly: "Data conflict noted (brief reason)"

*Slack Formatting Examples:*
• CORRECT: *Book Title* (bold headers)
• CORRECT: *Section Name* (bold section headers)
• CORRECT: • bullet point
• CORRECT: author@domain.com (plain text)
• WRONG: **Book Title** (double asterisks)
• WRONG: ### Header (markdown headers)
• WRONG: [text](url) (markdown links)
• WRONG: 1. Numbered list (use • instead)

Error Handling and Edge Cases:
• If no data is available for a query, respond: "No data available for this request"
• If multiple books match a search, show all matches with clear headers
• If data is incomplete, show available information and note what's missing
• If a book is not found, respond: "No profile found for [Book Title]"
• If conflicting data exists, note it briefly: "Data conflict noted (brief reason)"
• If query is ambiguous, ask for clarification: "Could you clarify which book you're asking about?"

Response Structure Principles:
• Start with a clear header that indicates what you're showing
• Use consistent formatting throughout the response
• Group related information logically
• Include only relevant information for the query type
• End with actionable next steps when appropriate
• Always follow the core formatting requirements above

Multi-Book Query Formatting:
• For queries covering multiple books (e.g., "what are all my ratings"):
  - Format each entry as: *[Book Title]*: [field value] or (na) if not available
  - Group entries logically (alphabetically by book title, or by rating/status/priority)
  - For ratings: Include ratings when available: *[Book Title]*: [rating]/5
  - For status: Show "Status: [status]" format per book
  - If more than 10 books, show top 10 and add summary line: "Also: X more books"
  - Keep each book entry concise (1-2 lines maximum per book)
  - Use bullet points (•) for each book entry

List Queries:
• For specific item type queries (e.g., "what are my favorite genres", "list all books"):
  - Show up to 8 items before "+N more" unless user requests more
  - Include relevant details like ratings, authors, or other context when available
  - Group by popularity, category, alphabetically, or by rating/status as appropriate
• For general list queries, show up to 6 items before "+N more" unless user requests more
• User override handling:
  - "show all" or "list all" → Show all available items without truncation
  - "top X" or "show top X" → Show exactly X items (e.g., "top 5" shows 5 items)
  - "first X" or "last X" → Show exactly X items from beginning or end
  - Always respect explicit user requests for specific quantities
'''

# -----------------------
# BOOK OUTPUT RULES
# -----------------------
BOOK_OUTPUT_RULES = '''
Book Profile Output Requirements:
• Use the Book Output Template structure ONLY for comprehensive book profile queries
• Start with *Book Title* (not ### Book Title) - ALWAYS replace with actual book title
• Adapt template sections based on query type:
  - Full profile queries: Use all sections (*Details*, *Review*, *Notes*, *Reading Timeline*)
  - Rating queries: Focus on *Details* section, include *Review* if relevant
  - Status queries: Focus on *Details* and *Reading Timeline* sections
  - Genre queries: Focus on *Details* section, include *Review* if relevant
• Follow all General Output Requirements above
• Length: up to 300 words per book
• Only show "(na)" for fields the user asked for or standard template fields
• In Details section, ALL field labels must be bold: *Author*:, *Rating*:, *Status*:, *Genre*:
• For empty sections, still use proper header format: "*Section Name:*" followed by "(na)" on next line

Multi-Book Responses:
• One section per book
• Sort by most recent activity date, then by rating: 5-star, 4-star, 3-star, 2-star, 1-star
• If more than 5 books, show the top 5 and list the rest in one compact line with counts
• Example: "Also: 3 more books (2 rated 4-star, 1 rated 3-star)"

Note: The Book Output Template is specifically for book profile queries. Other query types should use appropriate formats as defined in the General Output Rules.
'''

BOOK_LOGGING_RULES = '''
Book Logging Requirements (for book input/update queries):
• Use book logging format for book input requests (title, author, rating, status, review, notes)
• Start with *Book Title* followed by the logging information
• Format: *[Book Title]*: [logging information] or (na) if not available
• For author queries: Show "Author Name" format
• For multiple authors: List up to 3, then "+N more" if applicable
• Keep response concise - typically 1-3 lines maximum
• Do NOT use the full Book Output Template for logging requests

Examples:
• Query: "I just finished Scythe by Neal Shusterman, rated it 5/5" → Response: "*Scythe*: Logged as finished, rated 5/5 by Neal Shusterman"
• Query: "Started reading Dune today" → Response: "*Dune*: Status updated to 'reading'"
• Query: "Add notes: great world-building" → Response: "*[Book]*: Notes added - 'great world-building'"
'''

RECOMMENDATION_FORMAT = '''
Recommendation Format Requirements:
• Use recommendation format for book suggestion queries
• Start with *Recommendations* header
• Format each recommendation as: *[Book Title]* by [Author] - [Brief reason]
• Include rating and genre when available
• Group by similarity type (similar to X, same author, same genre)
• Show up to 5 recommendations before "+N more" unless user requests more
• Include brief explanation for each recommendation
• **CRITICAL**: NEVER recommend books that are already in the user's reading history
• Check reading history for book titles and authors to avoid duplicates
• If no recommendations available, suggest based on reading history or popular books

Examples:
• Query: "recommend something like Dune" → Response: "*Recommendations*: *Foundation* by Isaac Asimov - Similar epic sci-fi with complex world-building"
• Query: "what should I read next" → Response: "*Recommendations*: Based on your reading history..."
• Query: "suggest sci-fi books" → Response: "*Recommendations*: *Hyperion* by Dan Simmons - Award-winning sci-fi with multiple perspectives (avoiding books already read)"
'''

BOOK_OUTPUT_TEMPLATE = '''
*Book Output Template Structure:*

IMPORTANT: Use this template ONLY for comprehensive book profile queries, NOT for logging requests.

For book profile queries, use this structure (REPLACE [Book Title] with actual book title):

*[Book Title]*

*Details:*
• *Author*: [value or (na)] (value where feature=author)
• *Rating*: [value or (na)] (value where feature=rating)
• *Status*: [value or (na)] (value where feature=status)
• *Genre*: [value or (na)] (value where feature=genre) - Display multiple genres as comma-separated list
• *Started*: [value or (na)] (value where feature=start_date)
• *Finished*: [value or (na)] (value where feature=finish_date)

*Review:* (value where feature=review)
• Only 4 bullets (max) with dates in EDTF format when available, otherwise show as-is.
• Follow Date Handling Rules above for consistent formatting.
• Follow +N More Rules above for formatting
• Always format header as "*Review:*" (with colon)
• If no review, show "(na)" on the next line, not inline.

*Notes:* (value where feature=notes)
• Only 3 bullets (max) with dates in EDTF format when available, otherwise show as-is.
• Follow Date Handling Rules above for consistent formatting.
• Follow +N More Rules above for formatting
• Always format header as "*Notes:*" (with colon)
• If no notes, show "(na)" on the next line, not inline.

*Reading Timeline:* (value where feature=start_date, finish_date, status updates)
• When including dates, place them BEFORE the text: "[--07-29] string"
• Follow +N More Rules above for formatting
• If no timeline, show "(na)" on the next line, not inline.
• Always format as "*Reading Timeline:*" (with colon)

NOTE: Do NOT use this template for logging requests like "I just finished Scythe" - use book logging format instead.
'''

# -----------------------
# All Configuration Consolidation
# -----------------------
# This is the main CONFIG dictionary referenced at the top of the file
CONFIG = {
    "SYSTEM_PROMPT": SYSTEM_PROMPT,
    "ROUTING_RULES": ROUTING_RULES,
    "DATE_HANDLING_RULES": DATE_HANDLING_RULES,
    "PLUS_N_MORE_RULES": PLUS_N_MORE_RULES,
    "DATA_EXTRACTION_RULES": DATA_EXTRACTION_RULES,
    "AVAILABLE_FIELDS": AVAILABLE_FIELDS,
    "CANONICAL_FIELDS": CANONICAL_FIELDS,
    "FIELD_ALIASES": FIELD_ALIASES,
    "MULTIPLICITY_RULES": MULTIPLICITY_RULES,
    "CLARIFICATION_RULES": CLARIFICATION_RULES,
    "GENERAL_OUTPUT_RULES": GENERAL_OUTPUT_RULES,
    "BOOK_OUTPUT_RULES": BOOK_OUTPUT_RULES,
    "BOOK_LOGGING_RULES": BOOK_LOGGING_RULES,
    "RECOMMENDATION_FORMAT": RECOMMENDATION_FORMAT,
    "BOOK_OUTPUT_TEMPLATE": BOOK_OUTPUT_TEMPLATE,
}

# -----------------------
# Unified Query Constructor
# -----------------------
def _build_unified_query_template() -> str:    
    return '''
<SYSTEM_PROMPT>
{config_json}
</SYSTEM_PROMPT>

<DATA>
<PROFILE>
{profile}
</PROFILE>

<BOOK_DATA>
{context_block}
</BOOK_DATA>

<USER_QUERY>
{query}
</USER_QUERY>
</DATA>
'''.strip()

# -----------------------
# Book Query Constructor Class
# -----------------------
class BookQueryConstructor(BaseQueryConstructor):
    """Book Query Constructor optimized for book logging and recommendations"""
    
    def __init__(self):
        self.prompt_template = _build_unified_query_template()
        

    def create_query(
        self,         
        profile: Optional[str],
        context: Optional[str],
        query: str
    ) -> str:
        """Create a book query using the prompt template"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Validate input parameters
        if profile is not None and not isinstance(profile, str):
            raise ValueError("Profile must be a string or None")
        if context is not None and not isinstance(context, str):
            raise ValueError("Context must be a string or None")
            
        profile_str = profile or ""
        context_block = f"{context}\n\n" if context else ""

        try:
            # Get the config JSON for the template
            current_config = CONFIG.copy()
            current_config["CURRENT_DATE"] = _current_date_iso()
            try:
                config_json = json.dumps(current_config, indent=2)
            except (TypeError, ValueError) as e:
                logger.error(f"Error serializing CONFIG to JSON: {e}")
                config_json = '{"error": "Configuration serialization failed"}'
            
            result = self.prompt_template.format(
                config_json=config_json,
                profile=profile_str,
                context_block=context_block,
                query=query
            )
            return result
        except KeyError as e:
            logger.error(f"Template formatting error - missing placeholder: {e}")
            raise RuntimeError(f"Failed to format prompt due to missing key: {e}") from e
        except Exception as e:
            logger.error(f"Error creating book query: {e}")
            return f"{profile_str}\n\n{context_block}{query}"
