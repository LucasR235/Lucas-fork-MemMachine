"""
Book ingestion prompts for Intelligent Memory System
Handles book profiles with direct feature/value pairs
"""
from datetime import datetime
import zoneinfo, json

# -----------------------
# QUICK ACCESS TO MAIN CONFIG
# -----------------------
# 🔗 MAIN CONFIG: Jump to line ~505 (search for "All Configuration Consolidation")
# The CONFIG dictionary contains all prompt configuration and is the main entry point
# for modifying the Book prompt behavior.

# -----------------------
# Helper formatters
# -----------------------
def _features_inline_list() -> str:
    features = [
        "book_title", "author", "rating", "status", "review", "notes", 
        "genre", "style", "start_date", "finish_date", "reading_preferences",
        "user_preferences", "recommendation_reason"
    ]
    return ", ".join(features)

def _enum_list(enum_values) -> str:
    return ", ".join(f'"{v}"' for v in enum_values)

def _current_date_dow(tz="America/Los_Angeles") -> str:
    dt = datetime.now(zoneinfo.ZoneInfo(tz))
    return f"{dt.strftime('%Y-%m-%d')}[{dt.strftime('%a')}]"

# -----------------------
# SYSTEM PROMPT CONFIG
# -----------------------
SYSTEM_PROMPT = '''
You are an expert book profile manager that extracts and organizes reading data with precision. 
Follow the rules below to create accurate, structured book profiles.
'''

# -----------------------
# DATA CONFIG
# -----------------------
# --- Spreadsheet header  ---
FEATURES = [
    "book_title",
    "author",
    "rating",
    "status",
    "review",
    "notes",
    "genre",
    "style",
    "start_date",
    "finish_date",
    "reading_preferences",
    "user_preferences",
    "recommendation_reason",
]

FIELD_RULES = '''
Work ONLY with these features (use these exact keys; ignore others):
'''

FIELD_MAPPINGS = {
    "Book Title": "book_title",
    "Author": "author",
    "Rating": "rating",
    "Status": "status",
    "Review": "review",
    "Notes": "notes",
    "Genre": "genre",
    "Style": "style",
    "Start Date": "start_date",
    "Finish Date": "finish_date",
    "Reading Preferences": "reading_preferences",
    "User Preferences": "user_preferences",
    "Recommendation Reason": "recommendation_reason",
}

FIELD_TYPES = {
  "SINGLE_VALUED_REGULAR": ["book_title", "author", "rating", "status", "style", "start_date", "finish_date"],
  "MULTI_VALUED_REGULAR": ["genre", "user_preferences", "recommendation_reason"],
  "SINGLE_VALUED_TIMELINE": ["reading_preferences"],
  "MULTI_VALUED_TIMELINE": ["review", "notes"]
}

# --- Canonical enumerations ---
STATUS_ENUM = [
    "to-read", "reading", "finished", "abandoned", "on-hold"
]

RATING_ENUM = [
    "1", "2", "3", "4", "5"
]

GENRES = [
    "Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery", "Thriller",
    "Romance", "Historical Fiction", "Biography", "Memoir", "Self-Help", "Philosophy",
    "Poetry", "Drama", "Comedy", "Horror", "Young Adult", "Children's", "Classic",
    "Contemporary", "Literary Fiction", "Adventure", "Crime", "Dystopian", "Utopian"
]

# --- DATA Consolidation---
FIELD_ENUMERATIONS = {
    "STATUS_ENUM": STATUS_ENUM,
    "RATING_ENUM": RATING_ENUM,
    "GENRES": GENRES,
}

DATA_CONFIG = {
    "FIELD RULES": FIELD_RULES,
    "FIELDS": FEATURES,
    "FIELD MAPPINGS": FIELD_MAPPINGS,
    "FIELD TYPES": FIELD_TYPES,
    "FIELD ENUMERATIONS": FIELD_ENUMERATIONS,
}

# -----------------------
# ROUTING CONFIGURATIONS
# -----------------------
ROUTING_RULES = '''
EXTRACTION RULES:
- Book title + ANY book data → EXTRACT (always)
- Pure queries with NO book data → "no new information in user input"
- Data without book title → "no book title"
- Otherwise → extract following field rules below
'''

ROUTING_EXAMPLES = '''
**What constitutes actionable book data (ALWAYS EXTRACT):**
- Book title + rating (e.g., "Scythe 5/5", "Dune 4 stars", "Foundation rated 3")
- Book title + status (e.g., "finished Scythe", "started Dune", "abandoned Foundation")  
- Book title + review/notes (e.g., "Scythe: great world-building", "Dune: complex but rewarding")
- Book title + author information (e.g., "Scythe by Neal Shusterman", "Dune Frank Herbert")
- Book title + genre/style (e.g., "Scythe sci-fi", "Dune epic fantasy")
- ANY input with book title + book field data → EXTRACT, don't treat as query

**Frontend Structured Input Format (ALWAYS EXTRACT):**
- Structured data with fields: book_title, author, rating, status, start_date, finish_date, review, notes, preferences
- Format: "Book: [title] | Author: [author] | Rating: [rating]/5 | Status: [status] | Review: [review] | Notes: [notes] | Preferences: [preferences]"
- Date fields: "Started: [date] | Finished: [date]"
- Any structured input with these field patterns should be extracted

**Examples of NO new information** (pure queries):
- "scythe info" (asking for existing info)
- "what's my rating for Dune?" (requesting current rating)
- "tell me about my reading list" (general inquiry)
- "show me book details" (information request)

**Examples of information to extract** (actionable book data):
- "Finished Scythe by Neal Shusterman, rated it 5/5" (status + rating + author + book)
- "Started Dune today, sci-fi epic" (status + genre + book + start_date)
- "Foundation review: complex but fascinating world-building" (review + book)
- "Abandoned The Wheel of Time, too long" (status + book + notes)
- "Book: Scythe | Author: Neal Shusterman | Rating: 5/5 | Status: finished | Review: Great dystopian sci-fi" (structured input)
- Any message with book title + book field data should be extracted
'''

# -----------------------
# DATA EXTRACTION CONFIG
# -----------------------
DATE_EXTRACTION = '''
Date extraction and standardization:
- Use ISO format (YYYY-MM-DD) for complete dates
- Use EDTF format for incomplete dates: "M/D:" → "--MM-DD" (e.g., "7/28:" → "--07-28")
- Relative dates: "today" → current date, "yesterday" → current date - 1 day, "last week" → last Monday
- Timeline entries: format as "[EDTF_date] content" in value field
- If no date provided, use today's date. Do not omit date prefix entirely.
- Never invent missing dates or years

Timeline date handling (for review, notes, reading_preferences):
- EVERY timeline entry MUST have EDTF date at start of value: "[EDTF_date] content"
- EVERY timeline entry MUST have "date": "EDTF_format" field
- Date parsing priority (choose the MOST RELEVANT date for the timeline entry):
  1. **Event dates**: Parse relative dates that refer to when something WILL happen or DID happen (e.g., "finished yesterday" → use yesterday's date)
  2. **Sheet dates**: Use explicit dates that prefix content (e.g., "7/22: review" → use --07-22)
  3. **Message dates**: Only use the date the message was sent if no event date is specified
- **Sheet date format rules**:
  • "7/22:" → "--07-22" (month-day without year) - NEVER use <CURRENT_YEAR>-07-22
  • "4/28:" → "--04-28" (month-day without year) - NEVER use <CURRENT_YEAR>-04-28
  • "12/15:" → "--12-15" (month-day without year) - NEVER use <CURRENT_YEAR>-12-15
  • When input has "M/D:" format, ALWAYS use "--MM-DD" EDTF format
  • **NEVER add years to sheet dates** - keep them as month-day only format
  • ALL timeline entries with mm/dd without year MUST use EDTF format (--MM-DD), NEVER full year format (<CURRENT_YEAR>-MM-DD)
- Relative date examples:
  • "2/3: finished yesterday" → use yesterday's date, not 2/3
  • "early August" → "<CURRENT_YEAR>-08-01" (first day of month for "early")
  • "late August" → "<CURRENT_YEAR>-08-31" (last day of month for "late") 
  • "mid August" → "<CURRENT_YEAR>-08-15" (middle of month)
  • "August" → "<CURRENT_YEAR>-08" (month only)
- Process using above date extraction rules: yesterday, today, tomorrow, this week, last week, next week, this Tuesday, etc.
- If date completely unknown: use today unless content implies past events
- Multiple dated updates → split into separate "add" commands
'''

IDENTITY_EXTRACTION = '''
Book identification & normalization:
- Resolve the book in the user's message to ONE canonical book title using the book data provided in the Profile block.
- Normalize for matching (case/spacing/punctuation/abbreviations):
  • lowercase, trim, collapse extra spaces
  • strip punctuation at start/end; ignore commas, periods, hyphens in matching
  • expand common abbreviations:
      "vol" / "vol." → "volume"
      "bk" / "bk." → "book"
      "pt" / "pt." → "part"
      "ch" / "ch." → "chapter"
      "&" → "and"
- Matching policy:
  • Prefer exact match after normalization; otherwise pick the most similar by meaning/spelling from book titles present in the Profile data.
  • If several are close, prefer the longest, most specific name.
  • If no reasonable candidate exists, treat it as a NEW book and use the user-provided name verbatim.
'''

FIELD_EXTRACTION_GENERAL_RULES = '''
General extraction rules:
- **Tag field consistency**: MUST match the book being updated - no cross-book contamination allowed.
- **Extract actionable book data**: Any message containing book title + book field information should be extracted, NOT treated as a query.
'''

FIELD_EXTRACTION_SPECIFIC_FIELDS = ''' 
Field guidance:
**NON-TIMELINE FIELDS** (no date fields, no EDTF formatting):
- book_title: Book title (single-valued)
- author: Author name (single-valued) - ALWAYS extract if determinable
- rating: Allowed values: [{_enum_list(RATING_ENUM)}] (single-valued) - ALWAYS extract if determinable
- status: Allowed values: [{_enum_list(STATUS_ENUM)}] (single-valued) - ALWAYS extract if determinable
- genre: Multiple genres from [{_enum_list(GENRES)}] (multi-valued) - ALWAYS extract and derive from book content
  • Genre name variations: "sci-fi" → "Science Fiction", "fantasy" → "Fantasy", "non-fiction" → "Non-Fiction"
  • Extract when mentioned: space opera, epic fantasy, mystery thriller → related to Science Fiction/Fantasy/Mystery
  • Always extract genre mentions: "sci-fi novel", "fantasy epic", "mystery book" → appropriate genre
  • **CRITICAL**: If genre not explicitly mentioned, derive from book title, author, or content context
  • Common derivations: "Dune" → "Science Fiction", "Lord of the Rings" → "Fantasy", "1984" → "Dystopian"
  • **MULTI-GENRE SUPPORT**: Books can have multiple genres (e.g., "Science Fiction, Dystopian" for 1984)
  • Format multiple genres as comma-separated values: "Science Fiction, Fantasy, Adventure"
- style: Writing style description (single-valued)
- start_date / finish_date → EDTF format in value field (single-valued)

**SINGLE-VALUED TIMELINE FIELDS** (reading_preferences only):
- reading_preferences → user's reading preferences (single-valued, with date, timeline format)
  • Extract as reading_preferences when content contains preference indicators: "I like", "I prefer", "I enjoy", "I hate", "I dislike", "I love"
  • **CRITICAL**: Parse and separate each preference into individual entries
  • **Examples**: 
    - "I like sci-fi books" → reading_preferences: "Likes: Science Fiction"
    - "I prefer fantasy over romance" → reading_preferences: "Likes: Fantasy, Dislikes: Romance"
    - "I love mystery novels and hate horror" → reading_preferences: "Likes: Mystery, Dislikes: Horror"
  • **Format**: "Likes: [genre1, genre2] | Dislikes: [genre3, genre4] | Authors: [author1, author2]"

**MULTI-VALUED TIMELINE FIELDS** (review and notes):
- review / notes → timeline entries (multi-valued: preserve history)
  • EVERY timeline entry MUST have "[EDTF_date] content" format in value
  • EVERY timeline entry MUST have "date": "EDTF_format" field (never null)
    • **Field classification rules**:
    - review: Overall thoughts, opinions, recommendations about the book (e.g., "loved the characters", "plot was confusing")
    - notes: Specific details, quotes, observations, or technical notes that don't fit other categories
    **FIELD CLASSIFICATION:**
   1. **review**: Overall assessment, recommendation, general thoughts ("loved it", "disappointing", "highly recommend")
   2. **notes**: Specific details, quotes, technical observations, or background info
  • **Classification examples**:
    - "Great character development but slow pacing" → review
    - "Highly recommend this book" → review
    - "The world-building was incredible" → review
    - "Chapter 3 has the best dialogue" → notes
    - "Main character's name is Paul Atreides" → notes
    - "Set in the year 10191" → notes
    - "Author's writing style is very descriptive" → notes
    - "Plot twist in chapter 15" → notes
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
- **Only extract from USER INPUT**: Extract information ONLY from the user's new message, NOT from existing profile data provided as context.
- **Extract actionable book data**: Any message containing book title + book field information should be extracted, NOT treated as a query.
- Output commands ONLY for fields you can fill with a non-null value FROM THE USER INPUT.
- Do NOT include any null-valued add commands. Use "delete" commands to remove existing values.
- Focus on factual changes about book, author, and reading process FROM THE USER INPUT.
- Return ONLY a valid JSON object with commands (see ROUTING RULES above for exceptions).
- Keys must be "1","2","3", ... (strings).

**Tag field**: Always set "tag" to the book title if it can be extracted from the input. If the book cannot be determined or is uncertain, do NOT generate any commands and instead respond with: "no book title."
- The FIRST command MUST set the target book, e.g.:
  {{"command":"add","feature":"book_title","value":"<canonical book title>","tag":"<canonical book title>"}}

**EDTF dates REQUIRED for ALL timeline entries**: Every review, notes MUST have "[EDTF_date] content" format AND "date": "EDTF_format" field (never null).
**EDTF dates REQUIRED for reading_preferences**: reading_preferences MUST have "date": "EDTF_format" field (never null).
- Timeline fields (review, notes, reading_preferences) MUST include value: "[EDTF_date] content" and "date":"EDTF_format" field (never null).
- If date completely unknown: use today unless content implies past events

**Extract status FIRST**: Always determine and extract the reading status when possible from context clues IN THE USER INPUT. Extract status early in the command sequence.
**Separate timeline information**: Don't put everything in review - use appropriate fields (notes, review).
**Concise review entries**: Review should be 1-2 sentences summarizing overall thoughts, not paragraphs.
**Calculate ratings**: For star ratings, convert to 1-5 scale (e.g., "4 stars" → "4", "5/5" → "5").

When a message contains a new reading preference:
  1) Set the new Reading Preference (emit a "delete" then "add" for "reading_preferences" with the new value).
  2) Append a Review entry summarizing preference ONLY if it isn't a duplicate of the most recent review (case-insensitive substring dedupe).

**JSON Structure Rules:**
- DELETE commands: {{ "command": "delete", "feature": "field_name", "tag": "book_title", "author": "string|null" }}
- ADD commands (non-timeline): {{ "command": "add", "feature": "field_name", "value": "string", "tag": "book_title", "author": "string|null" }}
- ADD commands (timeline): {{ "command": "add", "feature": "timeline_field", "value": "[EDTF_date] content", "tag": "book_title", "author": "string|null", "date": "EDTF_format" }}
- *NEVER include "value" or "date" fields in DELETE commands**
- *NEVER include "date" field in non-timeline ADD commands**

**CRITICAL**: For ALL single-valued field updates, ALWAYS use delete-then-add pattern:
```
{{"command": "delete", "feature": "book_title", "tag": "BookTitle", "author": null}}
{{"command": "add", "feature": "book_title", "value": "BookTitle", "tag": "BookTitle", "author": null}}
```

- Only use these exact keys: review, notes, reading_preferences. "reading_preferences" is single-valued (use "delete" then "add"). "review" and "notes" are timeline fields (use "add").
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
0) New Book Profile:
Input: "I just finished Scythe by Neal Shusterman, rated it 5/5. Great dystopian sci-fi with amazing world-building."
Expected Output (assuming current date is 2025-01-20[Mon]):
{{
  "1": {{ "command": "delete", "feature": "book_title", "tag": "Scythe", "author": null }},
  "2": {{ "command": "add", "feature": "book_title", "value": "Scythe", "tag": "Scythe", "author": null }},
  "3": {{ "command": "add", "feature": "author", "value": "Neal Shusterman", "tag": "Scythe", "author": null }},
  "4": {{ "command": "add", "feature": "rating", "value": "5", "tag": "Scythe", "author": null }},
  "5": {{ "command": "add", "feature": "status", "value": "finished", "tag": "Scythe", "author": null }},
  "6": {{ "command": "add", "feature": "genre", "value": "Science Fiction, Dystopian", "tag": "Scythe", "author": null }},
  "7": {{ "command": "add", "feature": "review", "value": "[2025-01-20] Great dystopian sci-fi with amazing world-building", "tag": "Scythe", "date": "2025-01-20", "author": null }}
}}

1) Progress Update (existing profile):
Input: "Started reading Dune today. It's a complex sci-fi epic."
Expected Output (assuming current date is 2025-01-20):
{{
  "1": {{ "command": "delete", "feature": "book_title", "tag": "Dune", "author": null }},
  "2": {{ "command": "add", "feature": "book_title", "value": "Dune", "tag": "Dune", "author": null }},
  "3": {{ "command": "delete", "feature": "status", "tag": "Dune", "author": null }},
  "4": {{ "command": "add", "feature": "status", "value": "reading", "tag": "Dune", "author": null }},
  "5": {{ "command": "add", "feature": "start_date", "value": "2025-01-20", "tag": "Dune", "author": null }},
  "6": {{ "command": "add", "feature": "genre", "value": "Science Fiction", "tag": "Dune", "author": null }},
  "7": {{ "command": "add", "feature": "notes", "value": "[2025-01-20] Complex sci-fi epic", "tag": "Dune", "date": "2025-01-20", "author": null }}
}}

2) Sheet Date Format Example (Use EDTF --MM-DD):
Input: "Foundation update: 8/18: Finished reading 7/8: Great world-building 6/3: Started last week"
Expected Output (assuming current date is 2025-01-20):
{{
  "1": {{ "command": "delete", "feature": "book_title", "tag": "Foundation", "author": null }},
  "2": {{ "command": "add", "feature": "book_title", "value": "Foundation", "tag": "Foundation", "author": null }},
  "3": {{ "command": "add", "feature": "status", "value": "finished", "tag": "Foundation", "author": null }},
  "4": {{ "command": "add", "feature": "review", "value": "[--08-18] Finished reading", "tag": "Foundation", "date": "--08-18", "author": null }},
  "5": {{ "command": "add", "feature": "review", "value": "[--07-08] Great world-building", "tag": "Foundation", "date": "--07-08", "author": null }},
  "6": {{ "command": "add", "feature": "notes", "value": "[--06-03] Started last week", "tag": "Foundation", "date": "--06-03", "author": null }}
}}

**CRITICAL**: Notice all sheet dates use "--MM-DD" format, NOT "2025-MM-DD"!

3) Relative Date Parsing (Event vs Message Date):
Input: "2/3: Finished The Wheel of Time yesterday. Great fantasy series."
Expected Output (assuming current date is 2025-01-20[Mon]):
{{
  "1": {{ "command": "add", "feature": "book_title", "value": "The Wheel of Time", "tag": "The Wheel of Time", "author": null }},
  "2": {{ "command": "add", "feature": "status", "value": "finished", "tag": "The Wheel of Time", "author": null }},
  "3": {{ "command": "add", "feature": "genre", "value": "Fantasy", "tag": "The Wheel of Time", "author": null }},
  "4": {{ "command": "add", "feature": "review", "value": "[2025-01-19] Great fantasy series", "tag": "The Wheel of Time", "date": "2025-01-19", "author": null }}
}}

4) Sheet Date Format and Field Classification:
Input: "Reader is Alice. The Hobbit J.R.R. Tolkien 5/13: Loved the adventure 5/5: Great characters 4/28: Started reading last month"
Expected Output (assuming current date is 2025-01-20):
{{
  "1": {{ "command": "add", "feature": "book_title", "value": "The Hobbit", "tag": "The Hobbit", "author": "Alice" }},
  "2": {{ "command": "add", "feature": "author", "value": "J.R.R. Tolkien", "tag": "The Hobbit", "author": "Alice" }},
  "3": {{ "command": "add", "feature": "rating", "value": "5", "tag": "The Hobbit", "author": "Alice" }},
  "4": {{ "command": "add", "feature": "review", "value": "[--05-13] Loved the adventure", "tag": "The Hobbit", "date": "--05-13", "author": "Alice" }},
  "5": {{ "command": "add", "feature": "review", "value": "[--05-05] Great characters", "tag": "The Hobbit", "date": "--05-05", "author": "Alice" }},
  "6": {{ "command": "add", "feature": "notes", "value": "[--04-28] Started reading last month", "tag": "The Hobbit", "date": "--04-28", "author": "Alice" }}
}}

5) Frontend Structured Input Example:
Input: "Book: Scythe | Author: Neal Shusterman | Rating: 5/5 | Status: finished | Started: 2025-01-15 | Finished: 2025-01-20 | Review: Great dystopian sci-fi with amazing world-building | Notes: Complex characters and plot | Preferences: I love sci-fi books"
Expected Output (assuming current date is 2025-01-20):
{{
  "1": {{ "command": "delete", "feature": "book_title", "tag": "Scythe", "author": null }},
  "2": {{ "command": "add", "feature": "book_title", "value": "Scythe", "tag": "Scythe", "author": null }},
  "3": {{ "command": "add", "feature": "author", "value": "Neal Shusterman", "tag": "Scythe", "author": null }},
  "4": {{ "command": "add", "feature": "rating", "value": "5", "tag": "Scythe", "author": null }},
  "5": {{ "command": "add", "feature": "status", "value": "finished", "tag": "Scythe", "author": null }},
  "6": {{ "command": "add", "feature": "start_date", "value": "2025-01-15", "tag": "Scythe", "author": null }},
  "7": {{ "command": "add", "feature": "finish_date", "value": "2025-01-20", "tag": "Scythe", "author": null }},
  "8": {{ "command": "add", "feature": "genre", "value": "Science Fiction, Dystopian", "tag": "Scythe", "author": null }},
  "9": {{ "command": "add", "feature": "review", "value": "[2025-01-20] Great dystopian sci-fi with amazing world-building", "tag": "Scythe", "date": "2025-01-20", "author": null }},
  "10": {{ "command": "add", "feature": "notes", "value": "[2025-01-20] Complex characters and plot", "tag": "Scythe", "date": "2025-01-20", "author": null }},
  "11": {{ "command": "delete", "feature": "reading_preferences", "tag": "user", "author": null }},
  "12": {{ "command": "add", "feature": "reading_preferences", "value": "[2025-01-20] I love sci-fi books", "tag": "user", "date": "2025-01-20", "author": null }}
}}

6) Reading Preference Classification Example:
Input: "I love sci-fi books, especially space operas. Not a fan of romance novels."
Expected Output (assuming current date is 2025-01-20):
{{
  "1": {{ "command": "delete", "feature": "reading_preferences", "tag": "user", "author": null }},
  "2": {{ "command": "add", "feature": "reading_preferences", "value": "[2025-01-20] Likes: Science Fiction, Space Opera | Dislikes: Romance", "tag": "user", "date": "2025-01-20", "author": null }}
}}

7) Query/Reference Input (no new book information):
Input: "scythe info"
Expected Output: no new information in user input

8) Unknown Book (no commands generated):
Input: "Had a great reading experience today. The book was amazing. Highly recommend it."
Expected Output: no new information in user input

**CRITICAL: WRONG JSON STRUCTURE EXAMPLES (DO NOT USE):**
❌ WRONG - Delete with extra fields:
{{"command": "delete", "feature": "book_title", "tag": "Book", "author": null, "value": null, "date": null}}

❌ WRONG - Non-timeline with date field:
{{"command": "add", "feature": "book_title", "value": "Book", "tag": "Book", "author": null, "date": null}}

✅ CORRECT - Delete structure:
{{"command": "delete", "feature": "book_title", "tag": "Book", "author": null}}

✅ CORRECT - Non-timeline add:
{{"command": "add", "feature": "book_title", "value": "Book", "tag": "Book", "author": null}}

✅ CORRECT - reading_preferences add (single-valued with date):
{{"command": "add", "feature": "reading_preferences", "value": "[--05-19] I love fantasy books", "tag": "user", "author": null, "date": "--05-19"}}
'''

# -----------------------
# SUFFIX
# -----------------------
JSON_SUFFIX = """
Return ONLY a valid JSON object with the following structure:

NON-TIMELINE FIELDS (no "date" field):
ADD commands: { "command": "add", "feature": "field_name", "value": "string", "tag": "book_title", "author": "string|null" }
DELETE commands: { "command": "delete", "feature": "field_name", "tag": "book_title", "author": "string|null" }

SINGLE-VALUED FIELDS WITH DATE (reading_preferences only):
ADD commands: { "command": "add", "feature": "reading_preferences", "value": "[EDTF_date] content", "tag": "book_title", "author": "string|null", "date": "EDTF_format" }
DELETE commands: { "command": "delete", "feature": "reading_preferences", "tag": "book_title", "author": "string|null" }

TIMELINE FIELDS (MUST have "date" field):
ADD commands: { "command": "add", "feature": "review|notes", "value": "[EDTF_date] content", "tag": "book_title", "author": "string|null", "date": "EDTF_format" }
DELETE commands: { "command": "delete", "feature": "review|notes", "tag": "book_title", "author": "string|null" }

Commands:
- "add": Add new feature/value pair
- "delete": Remove existing feature/value pair (**REQUIRED before adding new value for ALL single-valued fields**)

**CRITICAL COMMAND PATTERN for single-valued fields**:
ALWAYS delete first, then add - regardless of whether field exists or not.

Single-valued fields requiring delete-then-add: book_title, author, rating, status, genre, style, start_date, finish_date, reading_preferences

Values:
- Use actual values when provided.
- Do NOT include any add command with a null value. Use "delete" commands to remove existing feature/value pairs.
- For ratings: 1-5 scale as string, e.g., "5" (no stars, no /5)
- For dates: Use EDTF (Extended Date/Time Format) to handle uncertainty and missing data
- EDTF format examples:
  • Complete: "2025-05-20" (year-month-day)
  • Month/Day only: "--05-19" (month-day, no year)
  • Day unknown: "2025-05-XX" (year-month, day unknown)
  • Month unknown: "2025-XX-20" (year-day, month unknown)
  • Year uncertain: "2025?-05-20" (year uncertain, month-day known)
- CRITICAL: NEVER invent years - if year is missing, use EDTF format
- For timeline entries: ALWAYS include "date" field with EDTF format AND "[EDTF_date] content" in value
- Use event dates when available (e.g., "finished yesterday" → use yesterday's date)
- If date completely unknown: use today unless content implies past events
- CRITICAL: NO timeline entry should have "date": null

Critical Rules:
- **JSON STRUCTURE**: DELETE commands have NO "value" or "date" fields; ADD commands include all required fields
- NON-timeline fields: NO "date" field in JSON
- Timeline fields: MUST have "date" field with EDTF format (never null)
- Timeline values: MUST start with "[EDTF_date] content"
- reading_preferences field: MUST have "date" field with EDTF format (never null) and use "[EDTF_date] content" format
- **SHEET DATES CRITICAL**: "8/18:" → "--08-18", "5/13:" → "--05-13", "4/28:" → "--04-28" (NEVER add years!)
- Early/mid/late: "early August" → "<CURRENT_YEAR>-08-01", "mid August" → "<CURRENT_YEAR>-08-15"
- Tag field: MUST match the book being updated (no cross-book contamination)
- **Field classification**: review=overall thoughts, notes=specific details/observations
- **Genre extraction**: "sci-fi"/"science fiction" → "Science Fiction", extract when space opera/fantasy mentioned
- No null values in "add" commands
"""

THINK_JSON_SUFFIX = """
First, analyze ONLY the user's input message to identify what NEW information they are providing.
CRITICAL: Do NOT extract information from existing profile data - only from the user's new message.
Follow the ROUTING RULES at the start of the prompt to determine the appropriate response.
For single-valued fields: **ALWAYS** first delete, then add - regardless of whether field exists.
For timeline entries: use add commands with EDTF dates - prioritize event dates over message dates.
Include concise 'review' when there is substantive thoughts/opinions IN THE USER INPUT.
CRITICAL: Timeline entries need "[EDTF_date] content" format AND "date": "EDTF_format" field (never null).
NEVER invent years - use EDTF uncertainty markers when needed.
Then return ONLY a valid JSON object with the following structure:

DELETE commands (no "value" or "date" fields):
{ "command": "delete", "feature": "field_name", "tag": "book_title", "author": "string|null" }

ADD commands - Non-timeline (no "date" field):
{ "command": "add", "feature": "field_name", "value": "string", "tag": "book_title", "author": "string|null" }

ADD commands - reading_preferences (single-valued timeline with 'date' field):
{ "command": "add", "feature": "reading_preferences", "value": "[EDTF_date] content", "tag": "book_title", "author": "string|null", "date": "EDTF_format" }

ADD commands - review or notes (multi-valued timeline with "date" field):
{ "command": "add", "feature": "review|notes", "value": "[EDTF_date] content", "tag": "book_title", "author": "string|null", "date": "EDTF_format" }
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
- tag: book title (broad category of memory)
- feature: book field name (book_title, author, rating, status, review, notes, etc.)
- value: detailed contents of the book field
- metadata: {{}}

You will output consolidated memories, which are json objects with 4 fields:
- tag: string (book title)
- feature: string (book field name)
- value: string (book field content)
- metadata: {{}}

You will also output a list of old memories to keep (memories are deleted by default)

Book-Specific Guidelines:
Book memories should not contain unrelated reading activities. Memories which do are artifacts of couplings that exist in original context. Separate them. This minimizes interference.
Book memories containing only redundant information should be deleted entirely, especially if they seem unprocessed or the information in them has been processed into timeline entries.

**Single-valued fields** (book_title, author, rating, status, genre, style, start_date, finish_date): If memories are sufficiently similar, but differ in key details, keep only the most recent or complete value. Delete older, less complete versions.
    - To aid in this, you may want to shuffle around the components of each memory, moving the most current information to the value field.
    - Keep only the key details (highest-entropy) in the feature name. The nuances go in the value field.
    - This step allows you to speculatively build towards more permanent book structures.

**Timeline fields** (review, notes, reading_preferences): If enough memories share similar timeline features (due to prior synchronization, i.e. not done by you), merge them chronologically and create consolidated timeline entries.
    - In these memories, the feature contains the book field type, and the value contains chronologically ordered timeline entries.
    - You can also directly transfer information to existing timeline lists as long as the new item has the same type as the timeline's items.
    - Don't merge timelines too early. Have at least three chronologically related entries in a non-gerrymandered category first. You need to find the natural groupings. Don't force it.

**Book-specific consolidation**:
All memories must have valid book title tags (no null tags allowed). Memories with different book tags should never be consolidated together.

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

Do not create new book feature names outside of the standard book schema: {_features_inline_list()}

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
