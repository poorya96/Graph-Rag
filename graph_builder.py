"""
graph_builder.py
────────────────
Step 2 of the pipeline.
 
Reads the CSV file and converts every row into a set of
Neo4j Nodes and Relationships, then saves them to the database.
 
Graph schema we create:
  (:Employee)   – one node per person
  (:Department) – one node per unique department
  (:Project)    – one node per unique project
  (:Skill)      – one node per unique skill (CSV uses ";" separator)
 
  (:Employee)-[:WORKS_IN]->(:Department)
  (:Employee)-[:REPORTS_TO]->(:Employee)       (if manager exists)
  (:Employee)-[:HAS_SKILL]->(:Skill)
  (:Employee)-[:WORKS_ON]->(:Project)
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

def build_graph() -> None:
    """Read CSV → build graph documents → save to Neo4j."""

# ── 1. Connect to Neo4j ──────────────────────────────────────────────────
    print("[graph_builder] Connecting to Neo4j …")
    graph = Neo4jGraph(
        url=config.NEO4J_URI,
        username=config.NEO4J_USERNAME,
        password=config.NEO4J_PASSWORD,
    )

# ── 2. Load CSV ──────────────────────────────────────────────────────────
    print(f"[graph_builder] Loading CSV from: {config.CSV_PATH}")
    df = pd.read_csv(config.CSV_PATH)
    print(f"[graph_builder] {len(df)} rows loaded.\n")
 
# ── 3. Build nodes & relationships ───────────────────────────────────────
    all_graph_documents:list[GraphDocument]=[]

    for _, row in df.iterrows():
        nodes: list[Node]=[]
        relationships: list[Relationship]=[]

     # ── Employee node ────────────────────────────────────────────────────
        emp_node = Node(
            type="Employee",
            id=_make_id(row["name"]),
            properties={
                "name": row["name"],
                "role": row["role"],
                "employee_id": row["employee_id"],
            },
        )
        nodes.append(emp_node)

        # ── Department node + WORKS_IN relationship ──────────────────────────
        dept_node = Node(
            type="Department",
            id=_make_id(row["department"]),
            properties={"name": row["department"]},
        )
        nodes.append(dept_node)
        relationships.append(
            Relationship(source=emp_node, target=dept_node, type="WORKS_IN")
        )
        # ── Project node + WORKS_ON relationship ─────────────────────────────
        if pd.notna(row.get("project")):
            proj_node = Node(
                type="Project",
                id=_make_id(row["project"]),
                properties={"name": row["project"]},
            )
            nodes.append(proj_node)
            relationships.append(
                Relationship(source=emp_node, target=proj_node, type="WORKS_ON")
            )
            # ── Skill nodes + HAS_SKILL relationships ────────────────────────────
        if pd.notna(row.get("skills")):
            for skill_name in row["skills"].split(";"):
                skill_name = skill_name.strip()
                skill_node = Node(
                    type="Skill",
                    id=_make_id(skill_name),
                    properties={"name": skill_name},
                )
                nodes.append(skill_node)
                relationships.append(
                    Relationship(
                        source=emp_node, target=skill_node, type="HAS_SKILL"
                    )
                )
 
        # ── REPORTS_TO relationship (resolved in second pass below) ──────────
        # Store manager name in properties for now; resolved after loop.

        if pd.notna(row.get("manager")):
            emp_node.properties["_manager_name"] = row["manager"]

        all_graph_documents.append(
            GraphDocument(node=nodes, relationships=relationships, source=None)
        )

    # ── 4. Second pass: add REPORTS_TO edges ─────────────────────────────────
    # Build a quick name→Node lookup

    emp_lookup:dict[str, Node]={}
    for gd in all_graph_documents:
        for node in gd.nodes:
            if node.type == "Employee":
               emp_lookup[node.properties["name"]]=node
    
    for gd in all_graph_documents:
        for node in gd.nodes:
            if node.type == "Employee" and "_manager_name" in node.properties:
                manager_name = node.properties.pop("_manager_name")
                if manager_name in emp_lookup:
                    gd.relationships.append(
                        Relationship(
                            source=node,
                            target=emp_lookup[manager_name],
                            type="REPORTS_TO",
                        )
                    )
# ── 5. Save everything to Neo4j ──────────────────────────────────────────
    print("[graph_builder] Saving graph documents to Neo4j …")
    graph.add_graph_documents(
        all_graph_documents,
        baseEntityLabel=True,   # adds __Entity__ label for easy querying
        include_source=False,
    )
    print("[graph_builder] ✅ Graph built successfully!\n")
    return graph
 
 
if __name__ == "__main__":
    build_graph()

            


      