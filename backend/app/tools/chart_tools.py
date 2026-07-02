from app.tools.registry import registry
CHART_TOOL_NAMES = ["generate_chart"] if registry.get("generate_chart") else []
