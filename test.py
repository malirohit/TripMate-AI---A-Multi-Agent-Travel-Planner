# from tools.tavily_tool import tavily_search
# from tools.flight_tool import search_flights
# from backend import run_travel_agent

# # res = tavily_search("Best hotels in India")
# # print(res)


# # res = search_flights("Plan a 7 days Nepal trip from Bangladesh")
# # print(res)

# user_input = input("Enter travel request: ")

# response = run_travel_agent(
#     user_input=user_input,
#     thread_id="test_user"
# )

# print("\nFINAL RESPONSE:\n")
# print(response["answer"])

import asyncio
from mcp_client import get_all_tools, tavily_mcp_search

if __name__ == "__main__":
    asyncio.run(tavily_mcp_search("Best hotels in India"))

