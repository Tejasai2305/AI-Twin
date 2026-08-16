from backend.embeddings.memory_vector_store import search_memory


def build_prompt(
    mode,
    history,
    notes_text,
    pdf_text,
    question,
):
    """
    Builds the final prompt for Gemini.

    Retrieved context is treated as evidence, not as automatically
    correct information.
    """

    # --------------------------------------------------
    # Search relevant long-term memories
    # --------------------------------------------------

    relevant_memories = search_memory(
        question,
        top_k=2,
    )

    if relevant_memories:
        memory_text = "\n".join(
            f"- {memory}"
            for memory in relevant_memories
        )
    else:
        memory_text = "None"

    print("\nRelevant Memories:")
    print(memory_text)
    print()

    # --------------------------------------------------
    # Formatting
    # --------------------------------------------------

    formatting_instructions = """
Formatting Rules:

- Always reply using GitHub-flavored Markdown.
- Wrap every code example inside fenced Markdown code blocks.
- Always specify the programming language for code blocks.
- Use headings when appropriate.
- Use bullet lists where useful.
- Use numbered lists for step-by-step instructions.
- Use Markdown tables when comparing things.
- Answer the user's actual question directly.
- Keep the answer focused.
"""

    # --------------------------------------------------
    # Grounding
    # --------------------------------------------------

    grounding_instructions = """
GROUNDING RULES:

- Retrieved notes, PDFs, memories, and conversation history are
  supporting context, not automatically correct answers.
- Use retrieved context when it is directly relevant.
- Do not assume two different terms refer to the same thing.
- Do not combine unrelated pieces of context to manufacture an answer.
- Never infer a secret code, password, identifier, or other specific
  private value from merely similar information.

PRIVATE INFORMATION RULE:

- For private, personal, secret, temporary, or user-specific
  information, only provide an answer when that information is
  explicitly supported by the relevant context.
- If a user-specific answer is not available in the context,
  clearly say that the information is not available.
- Do not guess private information.

GENERAL KNOWLEDGE RULE:

- For ordinary general-knowledge questions, use your general knowledge
  when the retrieved context does not contain the answer.
- Do not refuse a normal factual question simply because it is absent
  from the notes or PDFs.
"""

    # --------------------------------------------------
    # Memory
    # --------------------------------------------------

    memory_instructions = f"""
PRIVATE LONG-TERM MEMORY:

{memory_text}

MEMORY RULES:

- Treat these memories as private background context.
- Use them only when relevant.
- Do not list the memories.
- Do not summarize the memories.
- Do not mention that you searched memory.
- Do not mention the memory system.
- Do not bring up unrelated personal information.
- If a memory is irrelevant, ignore it completely.
"""

    # --------------------------------------------------
    # Conversation mode
    # --------------------------------------------------

    if mode == "conversation":

        return f"""
You are an intelligent AI assistant.

{formatting_instructions}

{grounding_instructions}

{memory_instructions}

CONVERSATION HISTORY:
{history}

Use conversation history when it is relevant.

If the question is an ordinary general-knowledge question and
conversation history does not contain the answer, use general knowledge.

If the question asks for private or user-specific information and
the information is not present in the available context, do not guess.

LATEST QUESTION:
{question}
"""

    # --------------------------------------------------
    # Knowledge mode
    # --------------------------------------------------

    elif mode == "knowledge":

        return f"""
You are an intelligent AI assistant.

{formatting_instructions}

{grounding_instructions}

{memory_instructions}

RELEVANT NOTES:
{notes_text}

RELEVANT PDF CONTENT:
{pdf_text}

Use notes and PDFs when they directly support the question.

Example:

Context:
"The secret project code name is Falcon-Blue-729."

Question:
"What is my temporary secret code?"

Do NOT conclude that the temporary secret code is Falcon-Blue-729.
Those are different concepts unless the context explicitly says
they are the same.

If the question is an ordinary general-knowledge question and the
documents do not contain the answer, use general knowledge.

If the question asks for private, personal, secret, temporary, or
user-specific information and the documents do not explicitly
support the answer, say that the information is not available.

Do not manufacture private information.

LATEST QUESTION:
{question}
"""

    # --------------------------------------------------
    # Hybrid mode
    # --------------------------------------------------

    else:

        return f"""
You are an intelligent AI assistant.

{formatting_instructions}

{grounding_instructions}

{memory_instructions}

CONVERSATION HISTORY:
{history}

RELEVANT NOTES:
{notes_text}

RELEVANT PDF CONTENT:
{pdf_text}

Use only context that is relevant to the user's question.

Priority:

1. Relevant conversation history
2. Relevant long-term memory
3. Relevant notes
4. Relevant PDF content
5. General knowledge

IMPORTANT:

The priority above does NOT mean that unrelated context should be
used.

Do not infer that two different identifiers, codes, names, projects,
or concepts are the same merely because they are similar.

For example:

Context:
"The secret project code name is Falcon-Blue-729."

Question:
"What is my temporary secret code?"

Correct behavior:
Do NOT answer Falcon-Blue-729 unless the context explicitly states
that it is also the temporary secret code.

For ordinary factual questions such as:

"What is the capital of France?"

answer using general knowledge even if the answer is not present in
the retrieved notes, PDFs, memories, or conversation history.

For private, personal, secret, temporary, or user-specific questions,
only answer when the relevant information is explicitly supported
by the available context.

If such private information is not available, say that it is not
available instead of guessing.

LATEST QUESTION:
{question}
"""