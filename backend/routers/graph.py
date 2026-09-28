from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_optional_user
from backend.services.graph_service import build_graph, get_graph_summary
from backend.services.memory_service import get_memory_detail, get_memory_chain

router = APIRouter()


def _uid(current_user):
    return current_user["id"] if current_user else None


@router.get("/graph")
def get_graph(include_inactive: bool = False, current_user=Depends(get_optional_user)):
    """
    Personal Knowledge Graph: User -> category -> individual facts,
    built live from stored memories. See graph_service.py for why
    this is computed on demand instead of stored separately.
    """
    try:
        return build_graph(include_inactive=include_inactive, user_id=_uid(current_user))
    except Exception as e:
        print("Graph build error:", e)
        raise HTTPException(status_code=500, detail="Unable to build knowledge graph.")


@router.get("/graph/summary")
def graph_summary(current_user=Depends(get_optional_user)):
    try:
        return get_graph_summary(user_id=_uid(current_user))
    except Exception as e:
        print("Graph summary error:", e)
        raise HTTPException(status_code=500, detail="Unable to summarize knowledge graph.")


@router.get("/graph/node/{node_id}")
def get_node_detail(node_id: str, current_user=Depends(get_optional_user)):
    """
    Node detail for clicking a node in the graph UI. For a fact node
    (id like 'memory-14'), returns the underlying memory plus its
    temporal chain so the UI can show history inline.
    """
    if node_id == "user":
        return {"id": "user", "type": "user", "label": "You"}

    if node_id.startswith("category-"):
        category = node_id[len("category-"):]
        return {"id": node_id, "type": "category", "label": category.replace("_", " ").title()}

    if node_id.startswith("memory-"):
        try:
            memory_id = int(node_id[len("memory-"):])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid node id.")

        detail = get_memory_detail(memory_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Memory not found.")

        if current_user is not None and detail["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Memory not found.")

        return {
            "id": node_id,
            "type": "fact",
            "memory": detail,
            "timeline": get_memory_chain(memory_id),
        }

    raise HTTPException(status_code=404, detail="Unknown node id.")
