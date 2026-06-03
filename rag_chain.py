"""
rag_chain.py
────────────
Step 3 of the pipeline.

Builds a Text-to-Cypher RAG chain:
  User question (natural language)
      → Groq LLM generates a Cypher query
      → Neo4j runs the query and returns results
      → Groq LLM writes a friendly answer from those results

Uses LangChain's GraphCypherQAChain, which handles the
two-LLM-call flow automatically.
"""

from langchain_groq import ChatGroq
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate

import config


# ── Cypher generation prompt ──────────────────────────────────────────────────
# This tells the LLM exactly how our graph is structured so it can
# write correct Cypher queries.
CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Cypher query writer for an FAQ knowledge graph.
Use ONLY the schema below to write queries. Do NOT make up properties or labels.

Schema:
{schema}

Graph Structure:
- (:FAQ) nodes contain: question, answer, category properties
- (:Category) nodes contain: name property
- (:FAQ)-[:BELONGS_TO]->(:Category) relationships

Rules:
- Always use MATCH, never CREATE or DELETE.
- Use case-insensitive substring matching with CONTAINS for question searches.
- Search in both question and answer properties for relevant content.
- Return the full FAQ node with all properties (question, answer, category).
- Return at most 10 results unless the user asks for more.
- If a question is very specific, search for related topics in FAQ questions/answers.

Question: {question}
Cypher query:
"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE,
)


# ── Answer generation prompt ──────────────────────────────────────────────────
QA_TEMPLATE = """
You are a helpful FAQ assistant for an Innovation Fund organization.
Use the FAQ results below to answer the user's question in a friendly, concise way.
Provide direct answers from the FAQ data.

If the results are empty, say you could not find relevant information in the FAQ.

Question: {question}
FAQ results: {context}

Answer:
"""

QA_PROMPT = PromptTemplate(
    input_variables=["question", "context"],
    template=QA_TEMPLATE,
)


def build_rag_chain(graph: Neo4jGraph) -> GraphCypherQAChain:
    """
    Build and return the GraphCypherQAChain.

    Parameters
    ----------
    graph : Neo4jGraph
        An already-connected Neo4j graph object.

    Returns
    -------
    GraphCypherQAChain
        Ready-to-use chain. Call chain.invoke({"query": "..."}).
    """
    print("[rag_chain] Initialising Groq LLM …")
    llm = ChatGroq(
        model=config.GROQ_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0,   # deterministic for Cypher generation
    )

    print("[rag_chain] Building GraphCypherQAChain …")
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
        qa_prompt=QA_PROMPT,
        verbose=True,        # prints the generated Cypher to console – great for learning
        return_intermediate_steps=True,
        allow_dangerous_requests=True,  # required by LangChain for Cypher execution
    )

    print("[rag_chain] Chain ready.\n")
    return chain