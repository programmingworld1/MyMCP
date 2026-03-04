from mcp.server.fastmcp import FastMCP

mcp = FastMCP("simple-server")

# This is our in-memory "database" — just a dictionary.
# Keys are document names, values are their contents.
docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}


# ── TOOLS ──────────────────────────────────────────────────────────────────────
# Tools are things the AI can DO (actions that can change state or return data).

@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Return the contents of a document by its ID (filename)."""
    if doc_id not in docs:
        return f"Error: '{doc_id}' not found. Available docs: {list(docs.keys())}"
    return docs[doc_id]


@mcp.tool()
def edit_doc(doc_id: str, new_content: str) -> str:
    """Overwrite the contents of a document with new_content."""
    if doc_id not in docs:
        return f"Error: '{doc_id}' not found. Available docs: {list(docs.keys())}"
    docs[doc_id] = new_content
    return f"'{doc_id}' updated successfully."


# ── RESOURCES ──────────────────────────────────────────────────────────────────
# Resources are things the AI can READ (like GET endpoints — no side effects).

@mcp.resource("docs://list")
def list_docs() -> str:
    """Return all document IDs."""
    return "\n".join(docs.keys())


@mcp.resource("docs://{doc_id}")
def get_doc(doc_id: str) -> str:
    """Return the contents of a specific document."""
    if doc_id not in docs:
        return f"Error: '{doc_id}' not found."
    return docs[doc_id]


# ── PROMPTS ────────────────────────────────────────────────────────────────────
# Prompts are reusable message templates the AI can fill in and send.

@mcp.prompt()
def rewrite_to_markdown(doc_id: str) -> str:
    """Prompt the AI to rewrite a document in clean Markdown format."""
    content = docs.get(doc_id, f"Document '{doc_id}' not found.")
    return f"Rewrite the following document in clean Markdown format:\n\n{content}"


@mcp.prompt()
def summarize_doc(doc_id: str) -> str:
    """Prompt the AI to summarize a document in a few sentences."""
    content = docs.get(doc_id, f"Document '{doc_id}' not found.")
    return f"Summarize the following document in 2-3 sentences:\n\n{content}"


if __name__ == "__main__":
    mcp.run()
