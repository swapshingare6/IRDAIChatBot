def error_node(state):
    print("❌ ERROR: ", state.get("error"))
    return {"handled": True}
