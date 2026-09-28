import ast
import operator


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError("Only numbers are allowed.")

    if isinstance(node, ast.BinOp):
        operator_function = _ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operator_function is None:
            raise ValueError("Operator not allowed.")

        left = _evaluate(node.left)
        right = _evaluate(node.right)

        return operator_function(left, right)

    if isinstance(node, ast.UnaryOp):
        operator_function = _ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operator_function is None:
            raise ValueError("Operator not allowed.")

        return operator_function(
            _evaluate(node.operand)
        )

    raise ValueError("Invalid mathematical expression.")


def execute(expression: str):
    """
    Safely evaluate a mathematical expression
    without using eval().
    """

    try:
        expression = expression.strip()

        if not expression:
            return {
                "success": False,
                "error": "Expression cannot be empty."
            }

        if len(expression) > 200:
            return {
                "success": False,
                "error": "Expression is too long."
            }

        tree = ast.parse(
            expression,
            mode="eval"
        )

        result = _evaluate(tree.body)

        return {
            "success": True,
            "result": result
        }

    except ZeroDivisionError:
        return {
            "success": False,
            "error": "Division by zero."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }