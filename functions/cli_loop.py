from prompt_toolkit import PromptSession
from agentConfig.agentLoop import agent_loop

def cli_loop():
    """
    Main input/output loop for the AI agent.
    It repeatedly prompts the user for input and passes it to the agent_loop.
    """
    session = PromptSession()
    history = []
    
    print("Welcome to the Holiday Planner! (Type 'exit' or 'quit' to leave)")
    
    while True:
        try:
            user_input = session.prompt("You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            
            response = agent_loop(user_input, history)
            if response is not None:
                print(response)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
