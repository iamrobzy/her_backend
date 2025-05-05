from zep_cloud import Message


def convert_to_zep_messages(conversation):
    messages = []
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
                    content += f"\n- {
                        tool_call.tool_name}: {
                        tool_call.params_as_json}"

        # Add tool results if present
        if hasattr(message_item, "tool_results") and message_item.tool_results:
            content += "\n\nTool Results:"
            for tool_result in message_item.tool_results:
                if hasattr(tool_result, "tool_name") and hasattr(
                    tool_result, "result_value"
                ):
                    content += f"\n- {
                        tool_result.tool_name}: {
                        tool_result.result_value}"

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
