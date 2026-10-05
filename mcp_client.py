import os
import sys
from pathlib import Path

import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq

# ==========================================
# Environment configuration
# ==========================================

os.environ["SSL_CERT_FILE"]  = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Automatically find the current project folder.
# This replaces the hard-coded Windows paths.
PROJECT_DIR = Path(__file__).resolve().parent
WEATHER_SERVER_PATH = PROJECT_DIR / "custom_weather_mcp_server.py"


# Preserve the complete Windows environment when starting
# local stdio MCP servers.
AVIATION_ENV = os.environ.copy()
AVIATION_ENV["AVIATION_STACK_API_KEY"] = (
    AVIATION_STACK_API_KEY or ""
)

WEATHER_ENV = os.environ.copy()
WEATHER_ENV["OPENWEATHER_API_KEY"] = (
    OPENWEATHER_API_KEY or ""
)

# ==========================================
# LLM
# ==========================================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)


# ==========================================
# MCP client configuration
# ==========================================
client = MultiServerMCPClient(
    {

       # Configurations to get remote or local MCP server's tools

       "tavily": {
           "transport" : "streamable_http",
           "url": (
                "https://mcp.tavily.com/mcp/"
                f"?tavilyApiKey={TAVILY_API_KEY}"
            )
       },

       "aviationstack": { # Local MCP
            "transport": "stdio",
            "command": "uvx",
            "args": [
                "aviationstack-mcp"
            ],
            "env": {
                "AVIATIONSTACK_API_KEY":AVIATION_STACK_API_KEY
            }
        },

        "weather" : { # Local Custom MCP
 
            "transport" : "stdio",

            # Use the same python environment where that runs app.py
            "command" : sys.executable, # # 3:42:00 See Tut as this contains error

            # Automatically run/use the custom_weather_mcp_server.py file in the same directory as the app.py file
            "args":[
                str(WEATHER_SERVER_PATH) 
            ],

            "env": WEATHER_ENV
        },


    }
)


# Right now we connect our MCP client to MCP server, 
# and now these client will have some kind of tools/funtions

# ==========================================
# Diagnostic function
# ==========================================

async def get_all_tools():

    tools = await client.get_tools()

    print("Available MCP tools:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")


# This returns tavily_search tool object
tavily_search_tool = None 

async def get_tavily_search_tool():
    global tavily_search_tool

    if tavily_search_tool is not None:
        return 

    tools = await client.get_tools()
    print("\nAvailable MCP Tools:")

    for tool in tools:
        print(tool.name)

    tavily_search_tool = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"
    )

# This function can be used to call the tavily_search tool with a query in backend.py
async def tavily_mcp_search(query:str):

    # await get_tavily_search_tool()
    await initialize_mcp()

    result = await tavily_search_tool.ainvoke(
        {
            "query":query
        }
    )

    return result
    # print(result)


search_tool = None
aviation_tools = {}

async def initialize_mcp():

    global search_tool, aviation_tools

    if search_tool is not None and aviation_tools:
        return

    tools = await client.get_tools()

    print("\nAvailable MCP Tools:\n")

    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

    search_tool = next(
        tool
        for tool in tools
        if tool.name != "tavily_search"
    )


#Filters all tools from which user should use from all the avaition tools available
async def aviation_mcp_call(
        tool_name:str,
        tool_args: dict = None
):
    
    tools = await client.get_tools()

    tool = next(
        t for t in tools
        if t.name == tool_name
    )

    result = await tool.ainvoke(
        tool_args or {}
    )

    return result



# ==========================================
# Weather MCP tools
# ==========================================

weather_tool = None
forecast_tool = None


async def initialize_weather_tools():
    global weather_tool
    global forecast_tool

    if (
        weather_tool is not None
        and forecast_tool is not None
    ):
        return

    if not WEATHER_SERVER_PATH.exists():
        raise FileNotFoundError(
            "Weather MCP server file was not found: "
            f"{WEATHER_SERVER_PATH}"
        )

    # Load only Weather.
    # Tavily and AviationStack will not be started.
    tools = await client.get_tools(
        server_name="weather"
    )

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    weather_tool = tools_by_name.get(
        "get_current_weather"
    )

    forecast_tool = tools_by_name.get(
        "get_forecast"
    )

    missing_tools = []

    if weather_tool is None:
        missing_tools.append(
            "get_current_weather"
        )

    if forecast_tool is None:
        missing_tools.append(
            "get_forecast"
        )

    if missing_tools:
        available_tools = ", ".join(
            tools_by_name.keys()
        )

        raise RuntimeError(
            "Missing Weather MCP tools: "
            f"{', '.join(missing_tools)}. "
            f"Available tools: "
            f"{available_tools or 'none'}"
        )


async def weather_mcp_search(city: str):

    await initialize_weather_tools()

    result = await weather_tool.ainvoke(
        {
            "city": city
        }
    )

    return result


async def forecast_mcp_search(city: str):
    await initialize_weather_tools()

    result = await forecast_tool.ainvoke(
        {
            "city": city
        }
    )

    return result


# ==========================================
# Destination extractor
# ==========================================


def extract_destination(query: str):
    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)

    return response.content.strip()