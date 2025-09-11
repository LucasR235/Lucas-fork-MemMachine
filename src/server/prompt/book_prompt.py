"""
Book ingestion prompts for Intelligent Memory System
Handles book profiles with direct feature/value pairs
"""
from datetime import datetime
import zoneinfo, json

# -----------------------
# QUICK ACCESS TO MAIN CONFIG
# -----------------------
# 🔗 MAIN CONFIG: Jump to line ~400 (search for "All Configuration Consolidation")
# The CONFIG dictionary contains all prompt configuration and is the main entry point
# for modifying the Book prompt behavior.

# -----------------------
# Helper formatters
# -----------------------
def _features_inline_list() -> str:
    return ", ".join(FEATURES)

def _enum_list(enum_values) -> str:
    return ", ".join(f"\"{v}\"" for v in enum_values)

def _current_date_dow(tz="America/Los_Angeles") -> str:
    dt = datetime.now(zoneinfo.ZoneInfo(tz))
    return f"{dt.strftime('%Y-%m-%d')}[{dt.strftime('%a')}]"

# -----------------------
# SYSTEM PROMPT CONFIG
# -----------------------
SYSTEM_PROMPT = '''
You are an AI assistant that manages book reading profiles based on user messages. Follow the rules and instructions provided below.
'''

# -----------------------
# DATA CONFIG
# -----------------------
# --- Core book fields ---
FEATURES = [
    "book_title", "author", "rating", "status", "additional_info", 
    "genre", "start_date", "finish_date",
    # User preference features
    "genre_preference", "reading_style", "content_preference", 
    "author_preference", "reading_habits", "recommendation_preference"
]

FIELD_RULES = '''
Work with these core book features. Be flexible - extract any book-related information naturally.
'''

FIELD_MAPPINGS = {
    "Book Title": "book_title",
    "Author": "author", 
    "Rating": "rating",
    "Status": "status",
    "Additional Information": "additional_info",
    "Genre": "genre",
    "Start Date": "start_date",
    "Finish Date": "finish_date",
    # User preference mappings
    "Genre Preference": "genre_preference",
    "Reading Style": "reading_style",
    "Content Preference": "content_preference",
    "Author Preference": "author_preference",
    "Reading Habits": "reading_habits",
    "Recommendation Preference": "recommendation_preference"
}

FIELD_TYPES = {
  "SINGLE_VALUED_REGULAR": ["book_title", "author", "rating", "status", "genre", "start_date", "finish_date"],
  "MULTI_VALUED_TIMELINE": ["additional_info", "genre_preference", "reading_style", "content_preference", "author_preference", "reading_habits", "recommendation_preference"]
}

# --- Flexible enumerations ---
STATUS_OPTIONS = ["to-read", "reading", "finished", "abandoned", "on-hold"]
RATING_OPTIONS = ["1", "2", "3", "4", "5"]
COMMON_GENRES = ["Science Fiction", "Fantasy", "Mystery", "Romance", "Thriller", "Non-Fiction", "Biography", "History", "Self-Help", "Philosophy", "Poetry", "Drama", "Comedy", "Horror", "Adventure", "Young Adult", "Children's"]

# --- DATA Consolidation---
DATA_CONFIG = {
    "FIELD RULES": FIELD_RULES,
    "FIELDS": FEATURES,
    "FIELD MAPPINGS": FIELD_MAPPINGS,
    "FIELD TYPES": FIELD_TYPES,
    "STATUS_OPTIONS": STATUS_OPTIONS,
    "RATING_OPTIONS": RATING_OPTIONS,
    "COMMON_GENRES": COMMON_GENRES,
}

# -----------------------
# ROUTING CONFIGURATIONS
# -----------------------
ROUTING_RULES = '''
- If user input contains identifiable book title + ANY book data → ALWAYS extract information (use book title as tag)
- If user input contains relevant user information extract using tag="user"
- Keep in mind the information can contain both book and user data. Extract both with appropriate tags.
- Only return "no new information in user input" for pure queries with NO book or user data
- Otherwise: extract book and or user information following the rules below

**CRITICAL DISTINCTION BETWEEN BOOK DATA AND USER DATA:**
- **Book Data** (tag = book title): Specific information about a particular book (title, author, rating, status, genre, dates, book-specific reviews, quotes, notes)
- **User Data** (tag = "user"): General reading preferences, habits, dislikes, likes that apply to multiple books or reading in general
- **Examples of User Data**: "I hate horror", "I love sci-fi", "I prefer short books", "I don't like romance novels", "I read mostly non-fiction"
- **Examples of Book Data**: "Dune was amazing", "Scythe had great character development", "Foundation is complex but rewarding"
'''

ROUTING_EXAMPLES = '''
**What constitutes actionable data (ALWAYS EXTRACT):**
- Book title + any details (rating, status, additional info, author, genre) → use book title as tag
- Book title + reading updates ("finished", "started", "abandoned") → use book title as tag
- Book title + reviews, thoughts, notes, or quotes → use book title as tag
- Reading preferences, general thoughts, or reading habits → use tag="user"
- Mixed input with both book and user data → extract both with appropriate tags
- ANY input with book title + book field data → EXTRACT, don't treat as query

**Examples of NO new information** (pure queries):
- "show me my books" (asking for existing info)
- "tell me about my reading list" (general inquiry)
- "show me book details" (information request)
- "what books do I have?" (information request)
- "help me with reading" (general help request)

**Examples of information to extract** (actionable data):
- "Finished Scythe by Neal Shusterman, rated it 5/5. Great dystopian sci-fi with complex themes" → extract all book data with book title as tag
- "Started Dune today" → extract book + status + date + genre with book title as tag
- "Foundation was complex but rewarding. The world-building was incredible" → extract book + additional info with book title as tag
- "I love sci-fi books, especially space operas" → extract as genre_preference with tag="user"
- "I hate horror novels, they're too scary for me" → extract as content_preference with tag="user"
- "I prefer short books under 300 pages" → extract as reading_style with tag="user"
- "I'm a big fan of Neil Gaiman's writing" → extract as author_preference with tag="user"
- "I read 2-3 books per month before bed" → extract as reading_habits with tag="user"
- "Finished Dune and I really enjoy epic fantasy novels" → extract both book data (Dune) and genre_preference with appropriate tags
- "Book: Scythe | Author: Neal Shusterman | Rating: 5/5 | Notes: Loved the character development" → extract structured data with book title as tag
- **CRITICAL RULE**: Any message with book title + book field data should be extracted, NOT treated as a query
- **USER DATA RULE**: General reading preferences, dislikes, and habits should always be tagged as "user", not as book data
'''

# -----------------------
# DATA EXTRACTION CONFIG
# -----------------------
DATE_EXTRACTION = '''
Date handling:
- Use ISO format (YYYY-MM-DD) for complete dates
- Use EDTF format for incomplete dates: "7/28:" → "--07-28"
- Relative dates: "today" → current date, "yesterday" → current date - 1 day
- Timeline entries: format as "[EDTF_date] content" in value field
- If no date provided, use today's date

Timeline entries:
- For additional_info: Include date at start: "[EDTF_date] [TYPE: content]" where TYPE is review, quote, or note
- For user preferences: Include date at start: "[EDTF_date] content"
- Include "date": "EDTF_format" field for all timeline entries
- Use event dates when available (e.g., "finished last week" → use last week's date)
- For user preferences without specific dates, use current date
'''

IDENTITY_EXTRACTION = '''
Book identification:
- Match book titles flexibly (case, spacing, punctuation)
- If similar book exists in profile, use that title
- If new book, use the title as provided
- Be generous with matching - "Dune" matches "Dune (1965)"
'''

FIELD_EXTRACTION_GENERAL_RULES = '''
Extraction rules:
- Extract any book-related information naturally
- Be flexible with field classification
- Focus on what the user is telling you about their reading
- **CRITICAL**: Extract information ONLY from the user's new message, NOT from existing profile data provided as context
'''

FIELD_EXTRACTION_SPECIFIC_FIELDS = ''' 
Field guidance:
**Basic fields:**
- book_title: Book title (single-valued)
- author: Author name (single-valued) - support multiple authors
- rating: 1-5 rating (single-valued) - extract when mentioned
- status: reading status (single-valued) - extract when mentioned
- genre: Book genres as single string in order of relevance (single-valued) - derive from content if not explicit
- start_date / finish_date: Reading dates (single-valued)

**Timeline field (additional_info):**
- additional_info: Unified field for all additional book information with intelligent subcategorization:
  * **Review**: Personal opinions, ratings, critiques, "I loved/hated this book", "amazing character development"
  * **Quote**: Direct quotes from the book, memorable passages, "The author wrote...", "My favorite line was..."
  * **Note**: Reading observations, plot points, "reminds me of...", "similar to...", "the ending was..."
- Format: "[EDTF_date] [TYPE: content]" where TYPE is one of: review, quote, note
- Supports multiple entries with dates
- Include date as "[EDTF_date] [TYPE: content]" and "date": "EDTF_format"
- AI should intelligently categorize content within this field based on context and language patterns

**User Preference Fields** (timeline fields with tag="user"):
- **genre_preference**: Genre likes/dislikes ("I love sci-fi", "I hate horror", "Fantasy is my favorite")
- **reading_style**: Reading pace, length, complexity ("I prefer fast-paced books", "I like short books under 300 pages")
- **content_preference**: Themes, settings, characters, tone ("I love time travel stories", "I prefer strong female protagonists")
- **author_preference**: Author likes/dislikes, writing style ("I love Neil Gaiman", "I prefer lyrical prose")
- **reading_habits**: Reading frequency, timing, context ("I read 2-3 books per month", "I read before bed")
- **recommendation_preference**: How they discover books, risk tolerance ("I trust Goodreads ratings", "I like trying new genres")
- Format: "[EDTF_date] content" with "date": "EDTF_format" and tag="user"
- These are separate timeline fields, not subcategories of additional_info
'''

# --- Extraction Consolidation---
DATA_EXTRACTION_CONFIG = {
    "DATE EXTRACTION": DATE_EXTRACTION,
    "IDENTITY EXTRACTION": IDENTITY_EXTRACTION,
    "FIELD EXTRACTION GENERAL RULES": FIELD_EXTRACTION_GENERAL_RULES,
    "FIELD EXTRACTION SPECIFIC FIELDS": FIELD_EXTRACTION_SPECIFIC_FIELDS,
}

# -----------------------
# OUTPUT CONFIGURATIONS
# -----------------------
OUTPUT_RULES = '''
Command Generation Rules:
- Extract information from the user's message naturally
- Output commands for fields you can fill from the user input
- Use "delete" then "add" for single-valued fields (book_title, author, rating, status, genre, start_date, finish_date)
- Use "add" for timeline fields (additional_info, genre_preference, reading_style, content_preference, author_preference, reading_habits, recommendation_preference)
- Return valid JSON with commands

**Tag field**: Set "tag" to the book title when extracting book-specific data. For general reading preferences or information without a specific book, use tag="user". For mixed input with both book and user data, extract both with appropriate tags. If no relevant information can be extracted, respond with: "no new information in user input."

**Timeline entries**: 
- For additional_info: Include date as "[EDTF_date] [TYPE: content]" and "date": "EDTF_format"
- For user preference fields: Include date as "[EDTF_date] content" and "date": "EDTF_format"

**CRITICAL**: Output commands ONLY for fields you can fill with a non-null value FROM THE USER INPUT. Do NOT include any null-valued add commands. Use "delete" commands to remove existing values.

**JSON Structure:**
- DELETE: {{ "command": "delete", "feature": "field_name", "tag": "book_title", "author": null }}
- ADD (non-timeline): {{ "command": "add", "feature": "field_name", "value": "string", "tag": "book_title", "author": null }}
- ADD (additional_info): {{ "command": "add", "feature": "additional_info", "value": "[EDTF_date] [TYPE: content]", "tag": "book_title", "author": null, "date": "EDTF_format" }}
- ADD (user preference): {{ "command": "add", "feature": "user_field_name", "value": "[EDTF_date] content", "tag": "user", "author": null, "date": "EDTF_format" }}
'''

OUTPUT_FORMAT = '''
Additional formatting guidelines:
- Use proper JSON formatting with consistent indentation
- Ensure all required fields are present in each command
- Validate command structure before output
'''

# --- Output Consolidation---
OUTPUT_CONFIG = {
    "OUTPUT_RULES": OUTPUT_RULES,
    "OUTPUT_FORMAT": OUTPUT_FORMAT,
}

IN_OUT_EXAMPLES = '''
Examples:
1) New Book:
Input: "Finished Scythe by Neal Shusterman, rated it 5/5. Great dystopian sci-fi with complex themes about mortality."
Output:
{{
  "1": {{ "command": "delete", "feature": "book_title", "tag": "Scythe", "author": null }},
  "2": {{ "command": "add", "feature": "book_title", "value": "Scythe", "tag": "Scythe", "author": null }},
  "3": {{ "command": "delete", "feature": "author", "tag": "Scythe", "author": null }},
  "4": {{ "command": "add", "feature": "author", "value": "Neal Shusterman", "tag": "Scythe", "author": null }},
  "5": {{ "command": "delete", "feature": "rating", "tag": "Scythe", "author": null }},
  "6": {{ "command": "add", "feature": "rating", "value": "5", "tag": "Scythe", "author": null }},
  "7": {{ "command": "delete", "feature": "status", "tag": "Scythe", "author": null }},
  "8": {{ "command": "add", "feature": "status", "value": "finished", "tag": "Scythe", "author": null }},
  "9": {{ "command": "delete", "feature": "genre", "tag": "Scythe", "author": null }},
  "10": {{ "command": "add", "feature": "genre", "value": "Science Fiction", "tag": "Scythe", "author": null }},
  "11": {{ "command": "add", "feature": "additional_info", "value": "[2025-01-20] [review: Great dystopian sci-fi with complex themes about mortality]", "tag": "Scythe", "date": "2025-01-20", "author": null }}
}}

2) Reading Update:
Input: "Started Dune today"
Output:
{{
  "1": {{ "command": "delete", "feature": "book_title", "tag": "Dune", "author": null }},
  "2": {{ "command": "add", "feature": "book_title", "value": "Dune", "tag": "Dune", "author": null }},
  "3": {{ "command": "delete", "feature": "status", "tag": "Dune", "author": null }},
  "4": {{ "command": "add", "feature": "status", "value": "reading", "tag": "Dune", "author": null }},
  "5": {{ "command": "delete", "feature": "start_date", "tag": "Dune", "author": null }},
  "6": {{ "command": "add", "feature": "start_date", "value": "2025-01-20", "tag": "Dune", "author": null }},
  "7": {{ "command": "delete", "feature": "genre", "tag": "Dune", "author": null }},
  "8": {{ "command": "add", "feature": "genre", "value": "Science Fiction", "tag": "Dune", "author": null }}
}}

3) General Reading Preferences:
Input: "I love sci-fi books, especially space operas and dystopian themes"
Output:
{{
  "1": {{ "command": "add", "feature": "genre_preference", "value": "[2025-01-20] I love sci-fi books, especially space operas and dystopian themes", "tag": "user", "date": "2025-01-20", "author": null }}
}}

4) Mixed Book and User Data:
Input: "Finished Dune and I really enjoy epic fantasy novels"
Output:
{{
  "1": {{ "command": "delete", "feature": "book_title", "tag": "Dune", "author": null }},
  "2": {{ "command": "add", "feature": "book_title", "value": "Dune", "tag": "Dune", "author": null }},
  "3": {{ "command": "delete", "feature": "status", "tag": "Dune", "author": null }},
  "4": {{ "command": "add", "feature": "status", "value": "finished", "tag": "Dune", "author": null }},
  "5": {{ "command": "add", "feature": "genre_preference", "value": "[2025-01-20] I really enjoy epic fantasy novels", "tag": "user", "date": "2025-01-20", "author": null }}
}}

5) No Book Info:
Input: "show me my books"
Output: no new information in user input

6) No Relevant Information:
Input: "Had a great reading experience today"
Output: no new information in user input

7) Different Types of Additional Information:
Input: "Dune was incredible! My favorite quote was 'Fear is the mind-killer.' The world-building reminded me of Foundation. I hate books with too much romance."
Output:
{{
  "1": {{ "command": "delete", "feature": "book_title", "tag": "Dune", "author": null }},
  "2": {{ "command": "add", "feature": "book_title", "value": "Dune", "tag": "Dune", "author": null }},
  "3": {{ "command": "add", "feature": "additional_info", "value": "[2025-01-20] [review: Dune was incredible!]", "tag": "Dune", "date": "2025-01-20", "author": null }},
  "4": {{ "command": "add", "feature": "additional_info", "value": "[2025-01-20] [quote: My favorite quote was 'Fear is the mind-killer.']", "tag": "Dune", "date": "2025-01-20", "author": null }},
  "5": {{ "command": "add", "feature": "additional_info", "value": "[2025-01-20] [note: The world-building reminded me of Foundation]", "tag": "Dune", "date": "2025-01-20", "author": null }},
  "6": {{ "command": "add", "feature": "content_preference", "value": "[2025-01-20] I hate books with too much romance", "tag": "user", "date": "2025-01-20", "author": null }}
}}

8) Detailed User Preference Categories:
Input: "I love sci-fi and fantasy, especially space operas. I prefer books under 400 pages and I'm a big fan of Neil Gaiman's writing style. I usually read 2-3 books per month before bed."
Output:
{{
  "1": {{ "command": "add", "feature": "genre_preference", "value": "[2025-01-20] I love sci-fi and fantasy, especially space operas", "tag": "user", "date": "2025-01-20", "author": null }},
  "2": {{ "command": "add", "feature": "reading_style", "value": "[2025-01-20] I prefer books under 400 pages", "tag": "user", "date": "2025-01-20", "author": null }},
  "3": {{ "command": "add", "feature": "author_preference", "value": "[2025-01-20] I'm a big fan of Neil Gaiman's writing style", "tag": "user", "date": "2025-01-20", "author": null }},
  "4": {{ "command": "add", "feature": "reading_habits", "value": "[2025-01-20] I usually read 2-3 books per month before bed", "tag": "user", "date": "2025-01-20", "author": null }}
}}
'''

# -----------------------
# SUFFIX
# -----------------------
JSON_SUFFIX = """
Return ONLY a valid JSON object with commands:

NON-TIMELINE FIELDS:
ADD: { "command": "add", "feature": "field_name", "value": "string", "tag": "book_title", "author": null }
DELETE: { "command": "delete", "feature": "field_name", "tag": "book_title", "author": null }

TIMELINE FIELDS:
ADD (additional_info): { "command": "add", "feature": "additional_info", "value": "[EDTF_date] [TYPE: content]", "tag": "book_title", "author": null, "date": "EDTF_format" }
ADD (user preferences): { "command": "add", "feature": "user_field_name", "value": "[EDTF_date] content", "tag": "user", "author": null, "date": "EDTF_format" }
DELETE: { "command": "delete", "feature": "field_name", "tag": "book_title_or_user", "author": null }

Where TYPE is one of: review, quote, note
User preference fields: genre_preference, reading_style, content_preference, author_preference, reading_habits, recommendation_preference

Rules:
- Use "delete" then "add" for single-valued fields (book_title, author, rating, status, genre, start_date, finish_date)
- Use "add" for timeline fields (additional_info, genre_preference, reading_style, content_preference, author_preference, reading_habits, recommendation_preference)
- Include dates as "[EDTF_date] [TYPE: content]" for additional_info and "[EDTF_date] content" for user preferences
- For user preferences, use tag="user" instead of book title
"""

THINK_JSON_SUFFIX = """
First, analyze ONLY the user's input message to identify what NEW information they are providing.
CRITICAL: Do NOT extract information from existing profile data - only from the user's new message.
Follow the ROUTING RULES at the start of the prompt to determine the appropriate response.
Extract book-specific data with book title as tag, user preferences with tag="user".
For mixed input, extract both with appropriate tags.
For single-valued fields: use "delete" then "add" - regardless of whether field exists.
For timeline entries: use add commands with EDTF dates - prioritize event dates over message dates.
Classify additional_info content into subcategories: [review:], [quote:], [note:]
For user preferences, use separate fields: genre_preference, reading_style, content_preference, author_preference, reading_habits, recommendation_preference
Then return ONLY a valid JSON object with commands.
"""

# -----------------------
# All Configuration Consolidation
# -----------------------
# 🔗 This is the main CONFIG dictionary referenced at the top of the file
CONFIG = {
  "SYSTEM_PROMPT": SYSTEM_PROMPT,
  "CURRENT_DATE": _current_date_dow(),
  "DATA_CONFIG": DATA_CONFIG,
  "ROUTING_RULES": ROUTING_RULES,
  "ROUTING_EXAMPLES": ROUTING_EXAMPLES,
  "DATA_EXTRACTION_CONFIG": DATA_EXTRACTION_CONFIG,
  "OUTPUT_CONFIG": OUTPUT_CONFIG,
  "IN_OUT_EXAMPLES": IN_OUT_EXAMPLES,
  "JSON_SUFFIX": JSON_SUFFIX,
  "THINK_JSON_SUFFIX": THINK_JSON_SUFFIX,
}

# -----------------------
# Unified Book prompt (handles both create and update scenarios)
# -----------------------
def _build_unified_book_prompt() -> str:
  return json.dumps(CONFIG, indent=2)

# -----------------------
# Data wrappers
# -----------------------
DEFAULT_CREATE_PROFILE_PROMPT_DATA = """
Profile: {profile}
Context: {context}
"""

DEFAULT_UPDATE_PROFILE_PROMPT_DATA = """
Profile: {profile}
Context: {context}
"""

# --- Final prompt strings exposed as constants (built from BOOK_FEATURES/enums) ---
UNIFIED_BOOK_PROMPT = _build_unified_book_prompt()

# For backward compatibility - both create and update use the same unified prompt
DEFAULT_CREATE_PROFILE_PROMPT = UNIFIED_BOOK_PROMPT
DEFAULT_UPDATE_PROFILE_PROMPT = UNIFIED_BOOK_PROMPT

# --- ProfileMemory expects these specific constant names ---
UPDATE_PROMPT = UNIFIED_BOOK_PROMPT + "\n\n" + THINK_JSON_SUFFIX

def _build_consolidation_prompt() -> str:
    return f"""
**OUTPUT FORMAT REQUIREMENT: You MUST return valid JSON with "consolidate_memories" and "keep_memories" keys. No exceptions.**

Your job is to perform memory consolidation for a book profile system.
Despite the name, consolidation is not solely about reducing the amount of memories, but rather, minimizing interference between book data points while maintaining reading history integrity.
By consolidating memories, we remove unnecessary couplings of book data from context, spurious correlations inherited from the circumstances of their acquisition.

You will receive a new book memory, as well as a select number of older book memories which are semantically similar to it.
Produce a new list of memories to keep.

A book memory is a json object with 4 fields:
- tag: book title (broad category of memory) or "user" for user preferences
- feature: book field name (book_title, author, rating, status, genre, start_date, finish_date, additional_info, genre_preference, reading_style, content_preference, author_preference, reading_habits, recommendation_preference)
- value: detailed contents of the book field
- metadata: {{}}

You will output consolidated memories, which are json objects with 4 fields:
- tag: string (book title or "user" for user preferences)
- feature: string (book field name)
- value: string (book field content)
- metadata: {{}}

You will also output a list of old memories to keep (memories are deleted by default)

Book-Specific Guidelines:
Book memories should not contain unrelated reading activities. Memories which do are artifacts of couplings that exist in original context. Separate them. This minimizes interference.
Book memories containing only redundant information should be deleted entirely, especially if they seem unprocessed or the information in them has been processed into timeline entries.

**Single-valued fields** (book_title, author, rating, status, genre, start_date, finish_date): If memories are sufficiently similar, but differ in key details, keep only the most recent or complete value. Delete older, less complete versions.
    - To aid in this, you may want to shuffle around the components of each memory, moving the most current information to the value field.
    - Keep only the key details (highest-entropy) in the feature name. The nuances go in the value field.
    - This step allows you to speculatively build towards more permanent book structures.

**Timeline fields** (additional_info, genre_preference, reading_style, content_preference, author_preference, reading_habits, recommendation_preference): If enough memories share similar timeline features (due to prior synchronization, i.e. not done by you), merge them chronologically and create consolidated timeline entries.
    - In these memories, the feature contains the book field type, and the value contains chronologically ordered timeline entries.
    - You can also directly transfer information to existing timeline lists as long as the new item has the same type as the timeline's items.
    - Don't merge timelines too early. Have at least three chronologically related entries in a non-gerrymandered category first. You need to find the natural groupings. Don't force it.
    - User preference fields (tag="user") should only be consolidated with other user preference fields of the same type.

**Book-specific consolidation**:
All memories must have valid tags (book title or "user"). Memories with different tags should never be consolidated together.
- Book memories (tag = book title) should only be consolidated with other memories for the same book
- User preference memories (tag = "user") should only be consolidated with other user preference memories

**EDTF date handling**:
Preserve EDTF date formats in timeline entries. When consolidating timeline memories, maintain chronological order based on EDTF dates.

Overall book memory life-cycle:
raw book updates -> clean book entries -> book entries sorted by book/field -> consolidated book profiles

The more book memories you receive for a single book, the more interference there is in the book system.
This causes cognitive load and makes reading tracking difficult. Cognitive load is bad.
To minimize this, under such circumstances, you need to be more aggressive about deletion:
    - Be looser about what you consider to be similar timeline entries. Some distinctions are not worth the energy to maintain.
    - Massage out the parts to keep and ruthlessly throw away the rest
    - There is no free lunch here! At least some redundant book information must be deleted!

Do not create new book feature names outside of the standard book schema: {", ".join(FEATURES)}

**CRITICAL: You MUST return valid JSON with EXACTLY these two keys: "consolidate_memories" and "keep_memories"**

The proper noop syntax (when no consolidation is needed):
{{
    "consolidate_memories": [],
    "keep_memories": []
}}

**REQUIRED OUTPUT FORMAT:**
<think>insert your chain of thought here</think>
{{
    "consolidate_memories": [
        {{
            "feature": "rating",
            "value": "5",
            "tag": "Scythe", 
            "metadata": {{}}
        }}
    ],
    "keep_memories": [123, 456]
}}

**IMPORTANT RULES:**
1. ALWAYS include both "consolidate_memories" and "keep_memories" keys
2. "consolidate_memories" should be an array (empty if no consolidation needed)
3. "keep_memories" should be an array of memory IDs to keep
4. Use proper JSON syntax with double quotes, not single quotes
5. Do not include any text outside the JSON object
""".strip()

CONSOLIDATION_PROMPT = _build_consolidation_prompt()