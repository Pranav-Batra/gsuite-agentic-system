from crewai import Agent, Task, Crew, LLM, Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import os
from dotenv import load_dotenv

load_dotenv('/Users/pranav/Desktop/GSuite-MCP/.env', override=True)

# Setup LLM (could be Claude or another, this part is fine)
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

    print(gcal_tools)
    print(gmail_tools)

    gcal_agent = Agent(
        role="Google Calendar API Expert",
        goal="Handle all operations related to interacting with Google Calendar",
        backstory="You are an expert in using the Google Calendar API",
        tools=gcal_tools,
        llm=llm,
        verbose=True
    )

    # Define DB Agent
    gmail_agent = Agent(
        role="Gmail API Expert",
        goal="Effectively interact with a person's mail through the Gmail API",
        backstory="You are a master of using the Gmail API. Your role is to interact with the Gmail API according to the user's wishes.",
        tools=gmail_tools,
        llm=llm,
        verbose=False
    )

    gdrive_agent = Agent(
        role="Google Drive API Expert",
        goal="Effectively interact with a person's files through the Google Drive API",
        backstory="You are a master of using the Google Drive API. Your role is to interact with the Google Drive API according to the user's wishes.",
        tools=gmail_tools,
        llm=llm,
        verbose=False
    )

    gcal_task = Task(
    description="Use google calendar according to the user's prompt: {user_prompt}",
    agent=gcal_agent,
    expected_output="Record of what you did with the Google Calendar API."
)

# DB Task
    gmail_task = Task(
        description="Execute this Gmail API related request from the user: {user_prompt}",
        agent=gmail_agent,
        expected_output="Record of what you did with the Gmail API."
    )

    gdrive_task = Task(
        description="Execute this Google Drive API related request from the user: {user_prompt}",
        agent=gmail_agent,
        expected_output="Record of what you did with the Google Drive API."
    )

    # Define Manager Agent (no tools)
    manager_agent = Agent(
        role="Task Manager",
        goal="Understand the user request and delegate to the appropriate agent.",
        backstory=(
            "You're responsible for coordinating between a Gmail expert, a Google Calendar expert, and a Google Drive expert. "
            "You never solve problems yourself — instead, you decide who is best suited for the task and pass the problem to them. "
            "The Gmail expert handles anything related to the Gmail API. The Google Calendar Expert handles anything related to the Google Calendar API. The Google Drive Expert handles anything related to the Google Drive API."
        ),
        llm=llm,
        verbose=True
    )


    # Create Crew and run
    crew = Crew(
        agents=[gmail_agent, gcal_agent, gdrive_agent],
        tasks=[gmail_task, gcal_task, gdrive_task],
        verbose=True,
        manager_llm = 'gemini/gemini-2.0-flash',
        process=Process.hierarchical,
        output_log_file='client/logs'
    )

    #EXAMPLE USER INPUTS
    user_prompt_1 = "Set up an event on my google calendar from Aug 17 2025 2:30PM to Aug 17 2025 3:00PM."
    user_prompt_2 = "Send an email from me to asphaltlord123@gmail.com with a subject line of 'Test'. Make the body of the message something related to programming."
    user_prompt_3 = "Create an event on August 7th, 2025, related to an NBA watch party starting at 5 PM and ending at 5:45. Then, send an email to asphaltlord123@gmail.com informing them of this event."
    user_prompt_4 = "What is ((12 * 7)^3)/4?"

    # Choose one to test:
    result = crew.kickoff(inputs={"user_prompt": user_prompt_1})
    print("\n FINAL RESULT:")
    print(result)
