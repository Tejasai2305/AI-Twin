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

    # Knowledge/document questions must NOT use global memory.
    # This prevents information from another document or conversation
    # from leaking into the current document-based answer.

    if mode == "knowledge":
        memory_text = "None"
    else:
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
- Use retrieved context only when it is directly relevant.
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
- Do not guess.

GENERAL KNOWLEDGE RULE:

- For ordinary general-knowledge questions, use general knowledge
  when appropriate.
- Do not use unrelated personal information to answer a question.
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

Use conversation history when it is directly relevant.

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

DOCUMENT GROUNDING RULES:

- For questions about the current document, use the retrieved PDF
  content as the primary and authoritative source.
- Do NOT use long-term memory to fill missing information.
- Do NOT use information from unrelated documents or conversations.
- Do NOT substitute information from the user's resume for information
  missing from the current PDF.
- Do NOT invent, omit, or substitute names, numbers, IDs, dates, or
  other explicitly stated values.
- When the user asks for ALL items, list ALL items explicitly supported
  by the retrieved PDF content.
- When the user asks for a count, count the explicitly listed items
  in the retrieved PDF content.
- Preserve names and identifiers exactly as they appear in the PDF.
- If the PDF does not contain enough information to answer completely,
  clearly state what information is missing.
- If the requested information is not present in the retrieved PDF
  content, say that it is not available in the current document.
- Do not use unrelated memory or previous-document information to
  complete the answer.

For example:

PDF:
"K. Rithik Sai [RA2311004020017],
D. Jayanth [RA2311004020015],
G. Sai Teja [RA2311004020018] and
K. Sasank [RA2311004020009]"

Question:
"List all the members of my minor project team with their names
and student IDs."

Correct behavior:
Return all four names and their corresponding student IDs exactly
as supported by the PDF.

IMPORTANT:

If the current PDF contains project information but does not contain
the user's technical skills, do NOT retrieve technical skills from
long-term memory or another document.

For example:

Current PDF:
"Compact Embedded Monitoring System for Industrial Hazard Detection"

Question:
"What are my technical skills?"

Correct behavior:
Say that the technical skills are not available in the current PDF.

Do not answer with technical skills found in the user's resume.

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

Use only context that is directly relevant to the user's question.

PRIORITY:

1. Relevant PDF content
2. Relevant notes
3. Relevant conversation history
4. Relevant long-term memory
5. General knowledge

IMPORTANT:

- The priority does NOT mean unrelated context should be used.
- Never use unrelated long-term memory to answer a document-specific
  question.
- Never use information from another document to answer a question
  about the current document.
- If the current PDF does not contain the requested information, say
  that it is not available in the current PDF.
- Do not fill missing document information using memories from other
  conversations or documents.
- Do not infer that two different identifiers, codes, names, projects,
  or concepts are the same merely because they are similar.

For ordinary factual questions such as:

"What is the capital of France?"

use general knowledge when appropriate.

For private, personal, secret, temporary, or user-specific questions,
only answer when the relevant information is explicitly supported by
the available context.

If such information is not available, say that it is not available
instead of guessing.

LATEST QUESTION:
{question}
"""