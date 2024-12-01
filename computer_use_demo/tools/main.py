import openai
import json
import os
from test_navigation_tool import windows_navigate
from function_schema import windows_navigate_function
from dotenv import load_dotenv
from rich import print as rr
# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key securely
openai.api_key = os.getenv('OPENAI_API_KEY')


def process_tool_calls(tool_calls):
    """Process all tool calls in parallel and return their results."""
    results = []
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "windows_navigate":
            # Execute the tool function and collect the result
            result = windows_navigate(**arguments)
            results.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call.id
            })
        else:
            # Handle unsupported functions gracefully
            result = f"Function '{function_name}' is not supported."
            results.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call.id
            })
    return results


def main():
    tools = [
        {
            "type": "function",
            "function": windows_navigate_function
        }
    ]

    # Initialize conversation with a system message
    messages = [
        {"role": "system", "content": "You are an assistant that can perform Windows navigation tasks."}
    ]

    while True:
        # Get user input
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting...")
            break

        # Add user input to the conversation
        messages.append({"role": "user", "content": user_input})

        try:
            # Make the first API call
            rr("messages:", messages)
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
            )

            # Extract the assistant's message
            assistant_message = response.choices[0].message
            messages.append(assistant_message.to_dict())
            if assistant_message.tool_calls:
                # Process all tool calls and get their results
                tool_responses = process_tool_calls(assistant_message.tool_calls)
                rr("tool response: ", tool_responses)
                # Append tool call results to the messages
                messages.extend(tool_responses)
                rr("messages", messages)
                # After processing all tool calls, make a follow-up API call
                follow_up_response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )

                # Extract and display the assistant's follow-up response
                follow_up_message = follow_up_response.choices[0].message
                messages.append(follow_up_message.to_dict())
                print(f"Assistant: {follow_up_message.content}")

            else:
                # Handle responses without tool calls
                messages.append(assistant_message.to_dict())
                print(f"Assistant: {assistant_message.content}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
