"""
main.py
───────
Entry point for the Graph RAG project.
 
Pipeline:
  1. Build the knowledge graph from CSV  (graph_builder.py)
  2. Build the RAG chain                 (rag_chain.py)
  3. Interactive Q&A loop               (this file)
 
Usage:
  python main.py              # run full pipeline (build graph + chat)
  python main.py --skip-build # skip graph building, go straight to chat
                               # (useful after you've already built the graph once)
"""
 
import argparse
import sys
 
from langchain_neo4j import Neo4jGraph
 
import config
from graph_builder import build_graph
from rag_chain import build_rag_chain
 
# Output file for storing conversation history
OUTPUT_FILE = "chat_results.txt"

# ── Sample questions shown at startup ────────────────────────────────────────
EXAMPLE_QUESTIONS = [
    "What services can knowledge-based companies use?",
    "What is a knowledge-based company?",
    "What are the fund's services and support?",
    "How to request fund services?",
    "What are the facility ceiling amounts determined by?",
    "What's the difference between facilities and investment?",
]
 
def connect_to_graph() -> Neo4jGraph:
    """Connect to Neo4j without rebuilding the graph."""
    print("[main] Connecting to existing Neo4j graph …")
    return Neo4jGraph(
        url=config.NEO4J_URI,
        username=config.NEO4J_USERNAME,
        password=config.NEO4J_PASSWORD,
        database=config.NEO4J_DATABASE,
    )
def run_interactive_loop(chain) -> None:
    """Start an interactive Q&A session in the terminal."""
    print("=" * 60)
    print("  Graph RAG – Interactive Q&A")
    print("  Type 'quit' or 'exit' to stop.")
    print("=" * 60)
    print("\nExample questions you can ask:")
    for q in EXAMPLE_QUESTIONS:
        print(f"  • {q}")
    print()
 
    # Open output file for writing results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Graph RAG – Chat Results\n")
        f.write("=" * 60 + "\n\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
 
        if not user_input:
            continue
 
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
 
        try:
            result = chain.invoke({"query": user_input})
 
            # GraphCypherQAChain returns a dict with:
            #   "result"              – the final human-readable answer
            #   "intermediate_steps"  – list with generated Cypher + raw DB result
            answer = result.get("result", "No answer returned.")
            steps  = result.get("intermediate_steps", [])
 
            print(f"\nAssistant: {answer}")
 
            # Write to file
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"User: {user_input}\n")
                f.write(f"Assistant: {answer}\n")
                
                # Optionally log the Cypher that was generated
                if steps:
                    cypher = steps[0].get("query", "")
                    if cypher:
                        f.write(f"[Cypher Query]: {cypher.strip()}\n")
                
                f.write("\n" + "-" * 60 + "\n\n")
 
            # Optionally show the Cypher that was generated
            if steps:
                cypher = steps[0].get("query", "")
                if cypher:
                    print(f"\n  [Cypher used]: {cypher.strip()}")
 
            print()
 
        except Exception as e:
            import traceback
            print(f"\n[ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            print()
            # Log error to file as well
            with open(OUTPUT_FILE, "a") as f:
                f.write(f"[ERROR] {type(e).__name__}: {e}\n")
                f.write(traceback.format_exc() + "\n\n")
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description="Graph RAG with Groq + Neo4j")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip graph building step (use if graph already exists in Neo4j)",
    )
    args = parser.parse_args()
 
    # ── Step 1: Build (or skip) ───────────────────────────────────────────────
    if args.skip_build:
        graph = connect_to_graph()
    else:
        print("Step 1/2 – Building knowledge graph from CSV …\n")
        graph = build_graph()
 
    # ── Step 2: Build RAG chain ───────────────────────────────────────────────
    print("Step 2/2 – Setting up RAG chain …\n")
    chain = build_rag_chain(graph)
 
    # ── Step 3: Chat ──────────────────────────────────────────────────────────
    run_interactive_loop(chain)
 
 
if __name__ == "__main__":
    main() 