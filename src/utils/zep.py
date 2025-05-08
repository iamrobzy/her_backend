from zep_cloud import Message


def convert_to_zep_messages(conversation):
    messages = []

    # Handle dict-style messages (direct API input)
    if isinstance(conversation, list):
        for message_item in conversation:
            role_type = "user"
            if (
                message_item.get("source") == "assistant"
                or message_item.get("source") == "ai"
            ):
                role_type = "assistant"

            messages.append(
                Message(
                    role_type=role_type,
                    content=message_item.get("message", ""),
                )
            )
        return messages

    # Handle string input (error case)
    if isinstance(conversation, str):
        try:
            import json

            # Try to parse it as JSON
            parsed = json.loads(conversation)
            if isinstance(parsed, list):
                return convert_to_zep_messages(parsed)
        except json.JSONDecodeError:
            # If it's not valid JSON, return a single message
            return [Message(role_type="user", content=conversation)]

    # Handle ElevenLabs conversation object
    if hasattr(conversation, "transcript"):
        for message_item in conversation.transcript:
            # Base message content
            content = ""
            if (
                hasattr(message_item, "message")
                and message_item.message is not None
            ):
                content = message_item.message
            elif hasattr(message_item, "result_value") and hasattr(
                message_item.result_value, "get"
            ):
                content = message_item.result_value.get("message", "")

            # Add tool calls if present
            if hasattr(message_item, "tool_calls") and message_item.tool_calls:
                content += "\n\nTool Calls:"
                for tool_call in message_item.tool_calls:
                    if hasattr(tool_call, "tool_name") and hasattr(
                        tool_call, "params_as_json"
                    ):
                        content += (
                            f"\n- {tool_call.tool_name}: "
                            f"{tool_call.params_as_json}"
                        )

            # Add tool results if present
            if (
                hasattr(message_item, "tool_results")
                and message_item.tool_results
            ):
                content += "\n\nTool Results:"
                for tool_result in message_item.tool_results:
                    if hasattr(tool_result, "tool_name") and hasattr(
                        tool_result, "result_value"
                    ):
                        content += (
                            f"\n- {tool_result.tool_name}: "
                            f"{tool_result.result_value}"
                        )

            messages.append(
                Message(
                    role_type=(
                        "assistant"
                        if message_item.role == "agent"
                        else message_item.role
                    ),
                    content=content,
                )
            )
        return messages

    # Could not process the conversation format
    raise ValueError(f"Unsupported conversation format: {type(conversation)}")
