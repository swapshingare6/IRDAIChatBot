import asyncio
from langgraph.graph import StateGraph, END
from nodes.scrape_irda import scrape_irda_circulars
from nodes.parse import parse_node
from nodes.embed import embed_node
from nodes.error_handler import error_node

from typing import TypedDict, Optional

class AgentState(TypedDict, total=False):
    error_msg: Optional[str]
    is_scrape_done: Optional[bool]
    is_parse_done: Optional[bool]
    is_embed_done: Optional[bool]
    start_urls: Optional[list[str]]
    filter_non_english: Optional[bool]

async def run_langgraph_agent_async():
    builder = StateGraph(AgentState)

    builder.add_node("scrape", scrape_irda_circulars)
    builder.add_node("parse", parse_node)
    builder.add_node("embed", embed_node)
    builder.add_node("error", error_node)

    builder.set_entry_point("scrape")
    builder.add_edge("scrape", "parse")
    builder.add_edge("parse", "embed")
    builder.add_edge("embed", END)
    builder.add_edge("error", END)

    graph = builder.compile()

    final_state = await graph.ainvoke({
        "start_urls": [
            "https://irdai.gov.in/rules"
        ],
        "filter_non_english": True
    })

    print("✅ Agent finished:", final_state)

if __name__ == "__main__":
    asyncio.run(run_langgraph_agent_async())
