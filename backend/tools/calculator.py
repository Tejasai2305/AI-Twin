def execute(expression: str):
    """
    Execute a mathematical expression safely.
    """

    try:
        allowed = "0123456789+-*/(). "

        if not all(c in allowed for c in expression):
            return {
                "success": False,
                "error": "Invalid characters."
            }

        result = eval(expression)

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }