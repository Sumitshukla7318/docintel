"""
Centralized prompt templates. Keeping these in one file makes iterating on
prompt quality fast without hunting through service logic.
"""

RAG_SYSTEM_PROMPT = """You are DocIntel, an AI assistant that answers questions strictly based on the \
provided document context. Follow these rules:

1. Only use information found in the CONTEXT section below. Do not use outside knowledge.
2. If the context does not contain enough information to answer, say so clearly instead of guessing.
3. Always be concise and direct.
4. When you use a fact from a specific source, reference it using its [Source N] marker inline.
5. Never fabricate document content, numbers, or quotes that are not present in the context."""


def build_rag_user_prompt(question: str, context_chunks: list[dict], conversation_history: str = "") -> str:
    context_blocks = []
    for i, chunk in enumerate(context_chunks, start=1):
        context_blocks.append(f"[Source {i}] (from \"{chunk['document_title']}\"):\n{chunk['content']}")

    context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant context was found."

    history_block = f"\nCONVERSATION HISTORY:\n{conversation_history}\n" if conversation_history else ""

    return f"""CONTEXT:
{context_text}
{history_block}
QUESTION: {question}

Answer the question using only the CONTEXT above. Cite sources like [Source 1] where relevant."""


QUERY_CONDENSE_PROMPT = """Given the conversation history and a follow-up question, rewrite the follow-up \
question as a standalone question that contains all necessary context. If the follow-up question is \
already standalone, return it unchanged. Return ONLY the rewritten question, nothing else.

CONVERSATION HISTORY:
{history}

FOLLOW-UP QUESTION: {question}

STANDALONE QUESTION:"""