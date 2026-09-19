def generate_answer(query, docs):
    """Simple RAG - return the most relevant doc directly with citations"""
    if not docs:
        return "No relevant information found. Source: Groww"

    # Get the top doc (most relevant)
    top_doc = docs[0]
    content = top_doc.page_content

    # Format nicely for the 4 questions
    q_lower = query.lower()

    if "exit load" in q_lower:
        # Extract exit load part
        return f"**{content}**\n\n*This is direct from retrieved documents.*"
    elif "sip" in q_lower:
        return f"**{content}**\n\n*This is direct from retrieved documents.*"
    elif "expense" in q_lower:
        return f"**{content}**\n\n*This is direct from retrieved documents.*"
    elif "lock" in q_lower:
        return f"**{content}**\n\n*This is direct from retrieved documents.*"
    else:
        return content

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])