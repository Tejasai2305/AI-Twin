from backend.embeddings.memory_vector_store import search_memory


def build_prompt(mode, history, notes_text, pdf_text, question):
    """
    Builds the final prompt for Gemini.

    Priority:
    1. Long-term memories
    2. Conversation history
    3. Notes
    4. PDFs
    5. Gemini's own knowledge
    """

    relevant_memories = search_memory(
        question,
        top_k=2,
    )

    if relevant_memories:
        memory_text = "\n".join(f"- {m}" for m in relevant_memories)
    else:
        memory_text = "None"

    print("\nRelevant Memories:")
    print(memory_text)
    print()

    # --------------------------------------------------
    # Conversation Mode
    # --------------------------------------------------
    if mode == "conversation":

        return f"""
You are an intelligent AI assistant.

Long-term Memories:
{memory_text}

Conversation History:
{history}

Instructions:
- Use the conversation history whenever it is relevant.
- Use long-term memories whenever they help answer the question.
- If the user's question is unrelated to the stored memories or history, answer using your own general knowledge.
- Never say "I don't have enough information" if you already know the answer.

Latest Question:
{question}
"""

    # --------------------------------------------------
    # Knowledge Mode
    # --------------------------------------------------
    elif mode == "knowledge":

        return f"""
You are an intelligent AI assistant.

Long-term Memories:
{memory_text}

Relevant Notes:
{notes_text}

Relevant PDF Content:
{pdf_text}

Instructions:
- Use memories if they are relevant.
- Use the notes and PDF content whenever they contain useful information.
- If the answer is not present in the memories, notes, or PDFs, answer using your own general knowledge.
- Do not refuse simply because the information is not in the documents.

Latest Question:
{question}
"""

    # --------------------------------------------------
    # Hybrid Mode
    # --------------------------------------------------
    else:

        return f"""
You are an intelligent AI assistant.

Long-term Memories:
{memory_text}

Conversation History:
{history}

Relevant Notes:
{notes_text}

Relevant PDF Content:
{pdf_text}

Instructions:
- First use long-term memories if they are relevant.
- Then use the conversation history.
- Then use the notes and PDF content.
- If none of them contain the answer, answer using your own general knowledge.
- Only say that you don't know when the answer truly cannot be determined.

Latest Question:
{question}
"""