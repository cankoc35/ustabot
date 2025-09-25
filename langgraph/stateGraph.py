from typing import Annotated
from typing_extensions import TypedDict
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
LOCAL_DB = os.environ["LOCAL_DB"] 

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver

from llm import llm
from tools import tools, tool_node




load_dotenv(Path(__file__).resolve().parent.parent / ".env")
LOCAL_DB = os.environ["LOCAL_DB"]  # or .get("LOCAL_DB")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    


graph_builder = StateGraph(State)
memory = InMemorySaver()
llm_with_tools = llm.bind_tools(tools)

# receives the current state as input, and returns an updated state.
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot",chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {"tools": "tools", "__end__": "__end__"}
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile(checkpointer=memory)


def stream_graph_updates(user_input: str):
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config={"configurable": {"thread_id": "1"}},
        stream_mode="values"
    )
    for event in events:
        # print("Assistant:", value["messages"][-1].content)
        event["messages"][-1].pretty_print()

while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)
    except:
        break
            

