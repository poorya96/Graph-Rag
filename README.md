# Graph RAG – FAQ Knowledge Base with AI Q&A

**Stack:** Python · LangChain · Neo4j · Groq (Llama 3)  
**Data:** FAQ CSV → Knowledge Graph → Natural Language Q&A

---

## What This Project Does

Convert your FAQ data into an intelligent knowledge graph that answers questions using AI:

```
faq_qa_pairs.csv
     │
     ▼
graph_builder.py   ← reads CSV, creates FAQ + Category nodes → saves to Neo4j
     │
     ▼
Neo4j Database     ← stores the FAQ knowledge graph with relationships
     │
     ▼
rag_chain.py       ← Text-to-Cypher RAG chain (Groq LLM)
     │              ├─ LLM converts question → Cypher query
     │              └─ LLM converts results → friendly answer
     ▼
main.py            ← interactive Q&A loop
```

**Example:**

- User: "How to apply?"
- AI: Converts to Cypher → finds matching FAQs → generates answer
- Output: "To apply, please email us at support@example.com"

---

## Project Structure

```
Graph rag/
├── main.py            ← entry point (run this)
├── config.py          ← loads .env settings
├── graph_builder.py   ← CSV → Neo4j graph (creates FAQ + Category nodes)
├── rag_chain.py       ← LangChain GraphCypherQAChain (question → Cypher → answer)
├── requirements.txt
├── .env               ← your API keys (never commit this!)
├── chat_results.txt   ← output file with conversation history
├── README.md
└── database/
    └── faq_qa_pairs.csv  ← your FAQ data (columns: question, answer, category)
```

---

## Step-by-Step Setup

### Step 1 – Get a Neo4j Database

You have two options:

**Option A – Free Cloud (recommended for beginners)**

1. Go to https://neo4j.com/cloud/platform/aura-graph-database/
2. Click "Start Free" → create an account
3. Click "New Instance" → choose "AuraDB Free"
4. **Save the password shown** – you only see it once!
5. Wait ~2 minutes for it to start
6. Copy the `neo4j+s://...` URI shown on the dashboard

**Option B – Local with Docker**

```bash
docker run \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yourpassword \
  neo4j:latest
```

Then open http://localhost:7474 to verify it's running.

---

### Step 2 – Get a Groq API Key

1. Go to https://console.groq.com
2. Sign up (free)
3. Click "API Keys" → "Create API Key"
4. Copy the key

---

### Step 3 – Configure .env

Open the `.env` file and fill in your values:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.1-70b-versatile
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io   ← from AuraDB
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
CSV_PATH=database/faq_qa_pairs.csv
```

**CSV Format** (3 columns required):

```
question,answer,category
"How to apply?","Email us at...",Admissions
"What is our mission?","We support...",About Us
```

> For local Docker: use `bolt://localhost:7687` as URI.

---

### Step 4 – Install Dependencies

```bash
cd graph_rag_project
pip install -r requirements.txt
```

---

### Step 5 – Run the Project

```bash
python main.py
```

What happens:

1. The CSV is read and converted into a graph in Neo4j
2. The RAG chain is built with the Groq LLM
3. An interactive Q&A prompt appears

**On subsequent runs** (graph already built):

```bash
python main.py --skip-build
```

---

### Step 6 – Ask Questions

Example questions (from actual project):

- `What services can knowledge-based companies use?`
- `What is a knowledge-based company?`
- `What are the fund's services and support?`
- `How to request fund services?`
- `What are the facility ceiling amounts determined by?`
- `What's the difference between facilities and investment?`

Or ask any question related to your FAQ data!

---

## Use Your Own CSV

Replace `database/faq_qa_pairs.csv` with any FAQ CSV. Required columns:

- `question` – the FAQ question
- `answer` – the FAQ answer
- `category` – topic/category of the question

The pipeline automatically:

- Creates `(:FAQ)` nodes with question, answer, category properties
- Creates `(:Category)` nodes for each unique category
- Links FAQs to categories with `[:BELONGS_TO]` relationships
- Generates Cypher queries to search across both question and answer text

---

## How This Project Works

1. **CSV → Graph (graph_builder.py)**
   - Reads FAQ CSV
   - Creates FAQ nodes (with question, answer, category properties)
   - Creates Category nodes
   - Creates BELONGS_TO relationships
   - Stores everything in Neo4j

2. **Graph → Cypher (rag_chain.py)**
   - LLM #1 reads your question in natural language
   - Converts it to a Cypher query using the graph schema
   - Example: "How to apply?" → `MATCH (f:FAQ) WHERE f.question CONTAINS 'apply' RETURN f`

3. **Cypher → Neo4j Results**
   - Runs the query on the Neo4j database
   - Returns matching FAQ nodes

4. **Results → Answer (rag_chain.py)**
   - LLM #2 reads the FAQ results
   - Writes a friendly, natural language answer
   - Saves conversation to `chat_results.txt`

---

## Why Graph RAG?

**vs. Traditional Vector RAG:**

- ✅ **Exact matches:** Find FAQs by category, not just similarity
- ✅ **Relationships:** Navigate between related FAQs through categories
- ✅ **Structured queries:** "Find all FAQs in category X" is precise
- ✅ **No hallucination:** LLM only generates answers from actual FAQ data

---

## Troubleshooting

| Problem                      | Solution                                                       |
| ---------------------------- | -------------------------------------------------------------- |
| `NEO4J_PASSWORD` not set     | Check your `.env` file is in project root                      |
| `Connection refused`         | Verify Neo4j is running and URI is correct                     |
| `CSV_PATH not found`         | Check path is `database/faq_qa_pairs.csv`                      |
| CSV has wrong columns        | Ensure columns are: `question`, `answer`, `category`           |
| LLM generates wrong Cypher   | Enable `verbose=True` in `rag_chain.py` to see generated query |
| Empty results for a question | Graph may not have matching FAQs; check your CSV data          |
| `GROQ_API_KEY invalid`       | Verify key from https://console.groq.com is correct            |

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
