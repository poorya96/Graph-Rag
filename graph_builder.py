"""
graph_builder.py
────────────────
Step 2 of the pipeline.
 
Reads the CSV file and converts every FAQ row into Neo4j nodes.
 
Graph schema we create:
  (:FAQ) – one node per FAQ entry with question, answer, and category
  (:Category) – one node per unique category
  
  (:FAQ)-[:BELONGS_TO]->(:Category)
"""
 
import pandas as pd
from langchain_neo4j import Neo4jGraph
from langchain_neo4j.graphs.graph_document import (
    GraphDocument,
    Node,
    Relationship,
)
 
import config
#  -------------------------------------------------------------------------
def _make_id(value: str) -> str:
    """Create a safe, lowercase node ID from any string."""
    return value.strip().lower().replace(" ", "-")

def build_graph() -> Neo4jGraph:
    """Read CSV → build graph documents → save to Neo4j."""

# ── 1. Connect to Neo4j ──────────────────────────────────────────────────
    print("[graph_builder] Connecting to Neo4j …")
    graph = Neo4jGraph(
        url=config.NEO4J_URI,
        username=config.NEO4J_USERNAME,
        password=config.NEO4J_PASSWORD,
        database=config.NEO4J_DATABASE,
       
    )

# ── 2. Load CSV ──────────────────────────────────────────────────────────
    print(f"[graph_builder] Loading CSV from: {config.CSV_PATH}")
    df = pd.read_csv(config.CSV_PATH)
    print(f"[graph_builder] {len(df)} rows loaded.\n")
 
# ── 3. Build nodes & relationships ───────────────────────────────────────
    all_graph_documents: list[GraphDocument] = []
    seen_categories: set[str] = set()

    for idx, row in df.iterrows():
        nodes: list[Node] = []
        relationships: list[Relationship] = []

        # ── FAQ node ─────────────────────────────────────────────────────
        question = row["question"]
        answer = row["answer"]
        category = row["category"]
        
        faq_node = Node(
            type="FAQ",
            id=_make_id(f"faq-{idx}"),
            properties={
                "question": question,
                "answer": answer,
                "category": category,
            },
        )
        nodes.append(faq_node)

        # ── Category node + BELONGS_TO relationship ──────────────────────────
        if category not in seen_categories:
            cat_node = Node(
                type="Category",
                id=_make_id(category),
                properties={"name": category},
            )
            nodes.append(cat_node)
            seen_categories.add(category)
            relationships.append(
                Relationship(source=faq_node, target=cat_node, type="BELONGS_TO")
            )
        else:
            # Category already exists, reference it
            cat_node = Node(
                type="Category",
                id=_make_id(category),
                properties={"name": category},
            )
            relationships.append(
                Relationship(source=faq_node, target=cat_node, type="BELONGS_TO")
            )

        all_graph_documents.append(
            GraphDocument(nodes=nodes, relationships=relationships, source=None)
        )

# ── 4. Save everything to Neo4j ──────────────────────────────────────────
    print("[graph_builder] Saving graph documents to Neo4j …")
    graph.add_graph_documents(
        all_graph_documents,
        baseEntityLabel=True,
        include_source=False,
    )
    print("[graph_builder] Graph built successfully!\n")
    return graph
 
 
if __name__ == "__main__":
    build_graph()

            


      