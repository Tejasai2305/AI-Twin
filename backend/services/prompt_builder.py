from backend.embeddings.memory_vector_store import search_memory


def build_prompt(mode, history, notes_text, pdf_text, question):

    relevant_memories = search_memory(
    question,
    top_k=2
  )

    if relevant_memories:
        memory_text = "\n".join(f"- {m}" for m in relevant_memories)
    else:
        memory_text = ""

    print("\nRelevant Memories:")
    print(memory_text)
    print()

    if mode == "conversation":
        return f"""
You are an AI assistant.

Long-term Memories:
{memory_text}

Conversation History:
{history}

Answer using the conversation history and the long-term memories.

If the answer is not present in either, say you don't have enough information.

Latest Question:
{question}
"""

    elif mode == "knowledge":
        return f"""
You are an AI assistant.

Long-term Memories:
{memory_text}

Relevant Notes:
{notes_text}

Relevant PDF Content:
{pdf_text}

Answer using the long-term memories and the provided knowledge.

If the answer is not present, say you don't have enough information.

Latest Question:
{question}
"""

    else:   # hybrid
        return f"""
You are an AI assistant.

Long-term Memories:
{memory_text}

Conversation History:
{history}

Relevant Notes:
{notes_text}

Relevant PDF Content:
{pdf_text}

Use the long-term memories, conversation history, and knowledge base.

If the answer is not present, say you don't have enough information.

Latest Question:
{question}
"""