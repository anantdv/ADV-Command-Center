from app.tools.registry import registry
SUPPORT_TOOL_NAMES = ["create_support_ticket"] if registry.get("create_support_ticket") else []
