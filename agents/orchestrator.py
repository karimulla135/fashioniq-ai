
import json

from config import get_anthropic_client, get_model
from agents.prompts import SYSTEM_PROMPT
from agents.tool_registry import TOOL_DEFINITIONS, execute_tool


class FashionIQAgent:
    """Claude-powered fashion business assistant."""

    def __init__(self, max_iterations=8):
        self.client = get_anthropic_client()
        self.model = get_model()
        self.max_iterations = max_iterations

    def run(self, user_message, conversation_history=None):
        """
        Process a user question using Claude tool calling.

        Returns:
            answer: Claude's final response.
            tool_calls: Tools executed and their inputs/results.
        """

        messages = list(conversation_history or [])
        messages.append({
            "role": "user",
            "content": user_message
        })

        tool_calls = []

        for iteration in range(self.max_iterations):

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages
            )

            # Claude has completed its response.
            if response.stop_reason == "end_turn":
                answer = "\n".join(
                    block.text
                    for block in response.content
                    if block.type == "text"
                )

                return {
                    "answer": answer,
                    "tool_calls": tool_calls,
                    "model": self.model
                }

            # Claude wants to execute one or more tools.
            if response.stop_reason == "tool_use":

                # Preserve Claude's complete response in conversation.
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                tool_results = []

                for block in response.content:

                    if block.type != "tool_use":
                        continue

                    tool_name = block.name
                    tool_input = block.input

                    print(f"\nExecuting tool: {tool_name}")
                    print(f"Input: {tool_input}")

                    # Execute the actual Python function.
                    result = execute_tool(tool_name, tool_input)

                    # Save execution details for the UI.
                    tool_calls.append({
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                        "tool_result": result
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                            default=str
                        )
                    })

                # Send the results back to Claude.
                if tool_results:
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                continue

            # Handle unexpected stop reasons.
            raise RuntimeError(
                f"Claude stopped unexpectedly: {response.stop_reason}"
            )

        raise RuntimeError(
            "Maximum tool-calling iterations reached. "
            "Please try a simpler question."
        )


if __name__ == "__main__":

    agent = FashionIQAgent()

    print("=" * 55)
    print("FASHIONIQ - AI FASHION BUSINESS ASSISTANT")
    print("=" * 55)

    question = input("\nAsk your business question: ")

    result = agent.run(question)

    print("\n" + "=" * 55)
    print("FASHIONIQ RESPONSE")
    print("=" * 55)

    print(result["answer"])

    print("\n" + "=" * 55)
    print("TOOLS EXECUTED")
    print("=" * 55)

    for call in result["tool_calls"]:
        print(f"\nTool: {call['tool_name']}")
        print(f"Input: {call['tool_input']}")

    print("\nModel:", result["model"])
