# gsuite-agentic-system
Agentic AI interface for interacting with Google Suite(Gmail, Google Calendar, Drive, etc.)

This project uses MCP servers to standardize LLM communication with common Google API services. Each MCP server comes with specific tools that can be used to perform common GSuite actions(i.e. sending an email, downloading a file from drive, or creating a Calendar event). To mimic an agentic system, CrewAI was used to set up a manager agent that chooses which tools specifically to interact with. 

For authorization, this project uses Google's oauth library to allow users to interact with the APIs from their account. It will also store each account's interactions in a secure S3 bucket so that they can view and download previous requests(not implemented yet). 

