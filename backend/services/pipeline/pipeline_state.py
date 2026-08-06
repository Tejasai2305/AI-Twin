from dataclasses import dataclass, field


@dataclass
class PipelineState:

    # Incoming request
    question: object

    # Tool Stage
    handled: bool = False
    tool_result: dict | None = None

    # Router
    mode: str = ""

    # Memory
    memories: str = ""

    # Conversation
    history: str = ""

    # Retrieval
    notes: str = ""
    pdf: str = ""
    pdf_results: list = field(default_factory=list)

    # Prompt
    prompt: str = ""

    # LLM
    answer: str = ""