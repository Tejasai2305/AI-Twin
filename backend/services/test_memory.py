from backend.services.memory_service import (
    add_memory,
    get_memories,
)

add_memory(
    "My name is Teja.",
    10
)

print(get_memories())