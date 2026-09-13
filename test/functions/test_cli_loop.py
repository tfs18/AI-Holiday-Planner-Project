from unittest.mock import patch
from functions.cli_loop import cli_loop

@patch('builtins.print')
@patch('functions.cli_loop.agent_loop')
@patch('functions.cli_loop.PromptSession')
def test_cli_loop_exit(mock_session_class, mock_agent_loop, mock_print):
    """Test that the loop exits when the user types 'exit'."""
    mock_session_class.return_value.prompt.side_effect = ['exit']
    cli_loop()
    mock_agent_loop.assert_not_called()

@patch('builtins.print')
@patch('functions.cli_loop.agent_loop')
@patch('functions.cli_loop.PromptSession')
def test_cli_loop_quit(mock_session_class, mock_agent_loop, mock_print):
    """Test that the loop exits when the user types 'quit'."""
    mock_session_class.return_value.prompt.side_effect = ['quit']
    cli_loop()
    mock_agent_loop.assert_not_called()

@patch('builtins.print')
@patch('functions.cli_loop.agent_loop')
@patch('functions.cli_loop.PromptSession')
def test_cli_loop_keyboard_interrupt(mock_session_class, mock_agent_loop, mock_print):
    """Test that the loop exits gracefully on KeyboardInterrupt."""
    mock_session_class.return_value.prompt.side_effect = KeyboardInterrupt
    cli_loop()
    mock_agent_loop.assert_not_called()

@patch('builtins.print')
@patch('functions.cli_loop.agent_loop')
@patch('functions.cli_loop.PromptSession')
def test_cli_loop_calls_agent_loop(mock_session_class, mock_agent_loop, mock_print):
    """Test that the agent_loop is called with user input."""
    mock_session_class.return_value.prompt.side_effect = ['hello', 'exit']
    mock_agent_loop.return_value = "Agent response"
    cli_loop()
    mock_agent_loop.assert_called_once_with('hello')

@patch('builtins.print')
@patch('functions.cli_loop.agent_loop')
@patch('functions.cli_loop.PromptSession')
def test_cli_loop_handles_empty_input(mock_session_class, mock_agent_loop, mock_print):
    """Test that the loop handles empty input and continues."""
    mock_session_class.return_value.prompt.side_effect = ['', 'exit']
    cli_loop()
    mock_agent_loop.assert_not_called()

@patch('builtins.print')
@patch('functions.cli_loop.agent_loop')
@patch('functions.cli_loop.PromptSession')
def test_cli_loop_prints_agent_response(mock_session_class, mock_agent_loop, mock_print):
    """Test that the agent's response is printed to the console."""
    mock_session_class.return_value.prompt.side_effect = ['hello', 'exit']
    mock_agent_loop.return_value = "Agent response"
    cli_loop()
    mock_print.assert_any_call("Agent response")

@patch('builtins.print')
@patch('functions.cli_loop.agent_loop')
@patch('functions.cli_loop.PromptSession')
def test_cli_loop_agent_error(mock_session_class, mock_agent_loop, mock_print):
    """Test that the loop handles unexpected exceptions from agent_loop."""
    mock_session_class.return_value.prompt.side_effect = ['hello', 'exit']
    mock_agent_loop.side_effect = Exception("Agent failed")
    cli_loop()
    # Should catch the exception and print an error message
    mock_print.assert_any_call("An unexpected error occurred: Agent failed")

@patch('builtins.print')
@patch('functions.cli_loop.agent_loop')
@patch('functions.cli_loop.PromptSession')
def test_cli_loop_handles_none_response(mock_session_class, mock_agent_loop, mock_print):
    """Test that the loop doesn't print anything if the agent returns None."""
    mock_session_class.return_value.prompt.side_effect = ['hello', 'exit']
    mock_agent_loop.return_value = None
    cli_loop()
    # Ensure print was not called with "None"
    for call in mock_print.call_args_list:
        assert call.args[0] is not None
        assert call.args[0] != "None"
