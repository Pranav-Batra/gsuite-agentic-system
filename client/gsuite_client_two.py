from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import os
from dotenv import load_dotenv

load_dotenv('/Users/pranav/Desktop/GSuite-MCP/.env', override=True)

# Setup LLM
llm = LLM(
    model="gemini/gemini-2.0-flash"
)

gmail_server_params = StdioServerParameters(
    command="python",
    args=["servers/gmail_server.py"]
)

gcal_server_params = StdioServerParameters(
    command="python",
    args=["servers/gcalendar_server.py"]
)

gdrive_server_params = StdioServerParameters(
    command = 'python',
    args = ['servers/gdrive_server.py']
)

server_params_list = [gmail_server_params, gcal_server_params, gdrive_server_params]

# Connect to the MCP servers and expose tools
with MCPServerAdapter(server_params_list) as tools:
    print(f"✅ Loaded MCP tools: {[tool.name for tool in tools]}")

    # Filter tools by topic
    gcal_tools = [tool for tool in tools if tool.name.startswith('gcal')]
    gmail_tools = [tool for tool in tools if tool.name.startswith('gmail')]
    gdrive_tools = [tool for tool in tools if tool.name.startswith('gdrive')]

    # --- AGENT DEFINITIONS ---

    gcal_agent = Agent(
        role="Google Calendar Specialist",
        goal="You are the go-to expert for all Google Calendar operations. Your job is to execute tasks related to Google Calendar with precision.",
        backstory="As a specialist, you don't decide what to do. You are given a specific task related to Google Calendar and you execute it perfectly using your tools.",
        tools=gcal_tools,
        llm=llm,
        verbose=True
    )

    gmail_agent = Agent(
        role="Gmail Specialist",
        goal="You are the go-to expert for all Gmail operations. Your job is to execute tasks related to Gmail with precision.",
        backstory="As a specialist, you don't decide what to do. You are given a specific task related to Gmail and you execute it perfectly using your tools.",
        tools=gmail_tools,
        llm=llm,
        verbose=True
    )

    gdrive_agent = Agent(
        role="Google Drive Specialist",
        goal="You are the go-to expert for all Google Drive operations. Your job is to execute tasks related to Google Drive with precision.",
        backstory="As a specialist, you don't decide what to do. You are given a specific task related to Google Drive and you execute it perfectly using your tools.",
        tools=gdrive_tools,
        llm=llm,
        verbose=True
    )

    # --- TASK DEFINITIONS ---

    # Define the specialist tasks first. Notice they don't have an agent assigned.
    # The manager will assign an agent to them at runtime.
    gcal_task = Task(
        description="Execute a Google Calendar request based on the user's prompt: {user_prompt}",
        expected_output="A confirmation and summary of the actions performed in Google Calendar."
    )

    gmail_task = Task(
        description="Execute a Gmail request based on the user's prompt: {user_prompt}",
        expected_output="A confirmation that the email was sent or the requested action was completed."
    )

    gdrive_task = Task(
        description="Execute a Google Drive request based on the user's prompt: {user_prompt}",
        expected_output="A confirmation and summary of the file operations performed in Google Drive."
    )
    
    # --- MANAGER AGENT AND ROUTER TASK ---
    
    # This is the router task that the manager will execute.
    # It explicitly includes the other tasks in its context, allowing the manager
    # to delegate to them directly.
    router_task = Task(
        description="""Analyze the user's prompt and delegate it to the appropriate specialist task.
        You must use one of the available tasks from your context. Do not perform the task yourself.

        User Prompt: {user_prompt}""",
        expected_output="The final result from the specialist agent after successful delegation and execution.",
        # NEW: Pass the specialist tasks into the context
        context=[gcal_task, gmail_task, gdrive_task],
    )
    
    manager_agent = Agent(
        role="G-Suite Task Manager",
        goal="Analyze user requests and delegate them to the correct specialist agent by assigning them the appropriate task.",
        backstory=(
            "You are the central coordinator. Your job is to look at the user's request and the available specialist tasks (from your context). "
            "You must match the request to the correct task and delegate it to the appropriate specialist agent. "
            "For complex requests involving multiple steps (e.g., create a calendar event AND send an email), you will delegate the tasks sequentially."
        ),
        llm=llm,
        verbose=True,
    )

    # --- CREW DEFINITION ---
    crew = Crew(
        # The manager MUST be the first agent in the list for this structure to work.
        agents=[manager_agent, gcal_agent, gmail_agent, gdrive_agent],
        # The manager will start with the router_task, which has the other tasks in its context.
        tasks=[router_task],
        verbose=True,
        manager_llm=llm,
        process=Process.hierarchical,
        output_log_file='client/logs/'
    )

    # --- EXAMPLE USER INPUTS ---
    user_prompt_1 = "Set up an event on my google calendar for tomorrow at 2 PM for a 'Team Sync'."
    user_prompt_2 = "Send an email from me to asphaltlord123@gmail.com with a subject line of 'Important Update'. Make the body 'Please review the attached document.'."
    user_prompt_3 = "Create a new event on my calendar for September 1st, 2025, at 10 AM called 'Project Kickoff'. After that is done, send an email to asphaltlord123@gmail.com informing them that the kickoff meeting has been scheduled."
    user_prompt_4 = "Search my Google Drive for images with 'rent' in the title. Download the first result from your search." # A prompt the manager should reject as it doesn't fit any specialist task.

    # --- EXECUTE THE CREW ---
    result = crew.kickoff(inputs={"user_prompt": user_prompt_4})
    
    print("\n\n########################")
    print("## FINAL CREW RESULT ##")
    print("########################")
    print(result)