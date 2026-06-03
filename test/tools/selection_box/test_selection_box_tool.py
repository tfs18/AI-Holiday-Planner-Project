import pytest
from unittest.mock import patch
from tools.selection_box.selection_box_tool import selection_box_tool

@pytest.fixture
def sample_holidays():
    return [
        {
            "ranking": 1,
            "city": "Paris",
            "date": "2026-06-15",
            "weather": "Sunny",
            "score": 95
        },
        {
            "ranking": 2,
            "city": "London",
            "date": "2026-06-16",
            "weather": "Rainy",
            "score": 70
        }
    ]

def test_selection_box_tool_success(sample_holidays):
    """Test successful selection of a holiday."""
    with patch("tools.selection_box.selection_box_tool.choice") as mock_choice:
        # Simulate user selecting the first holiday
        mock_choice.return_value = sample_holidays[0]
        
        result = selection_box_tool(sample_holidays)
        
        assert result["status"] == "success"
        assert result["data"] == sample_holidays[0]
        assert result["data"]["city"] == "Paris"

def test_selection_box_tool_cancel(sample_holidays):
    """Test user selecting the cancel option."""
    with patch("tools.selection_box.selection_box_tool.choice") as mock_choice:
        # Simulate user selecting 'None' (Cancel)
        mock_choice.return_value = None
        
        result = selection_box_tool(sample_holidays)
        
        assert result["status"] == "failure"
        assert "cancelled" in result["message"]

def test_selection_box_tool_empty_list():
    """Test behavior with an empty input list."""
    result = selection_box_tool([])
    assert result["status"] == "failure"
    assert "No holiday destinations" in result["message"]

def test_selection_box_tool_not_a_list():
    """Test behavior when input is not a list (e.g., a string)."""
    # For a string, it will iterate over characters, find no dicts, and return a specific validation error.
    result = selection_box_tool("not a list") # type: ignore
    assert result["status"] == "failure"
    assert "No valid holiday dictionaries" in result["message"]

def test_selection_box_tool_invalid_items():
    """Test behavior with a list containing non-dictionary items."""
    invalid_list = ["not a dict", None, 123]
    result = selection_box_tool(invalid_list) # type: ignore
    
    assert result["status"] == "failure"
    assert "No valid holiday dictionaries" in result["message"]

def test_selection_box_tool_partial_invalid_items(sample_holidays):
    """Test that it filters out invalid items and still allows selection of valid ones."""
    mixed_list = [None, sample_holidays[0], "invalid"]
    
    with patch("tools.selection_box.selection_box_tool.choice") as mock_choice:
        mock_choice.return_value = sample_holidays[0]
        
        result = selection_box_tool(mixed_list) # type: ignore
        
        assert result["status"] == "success"
        assert result["data"] == sample_holidays[0]

def test_selection_box_tool_keyboard_interrupt(sample_holidays):
    """Test handling of Ctrl+C."""
    with patch("tools.selection_box.selection_box_tool.choice") as mock_choice:
        mock_choice.side_effect = KeyboardInterrupt
        
        result = selection_box_tool(sample_holidays)
        
        assert result["status"] == "failure"
        assert "aborted" in result["message"]

def test_selection_box_tool_eof_error(sample_holidays):
    """Test handling of Ctrl+D."""
    with patch("tools.selection_box.selection_box_tool.choice") as mock_choice:
        mock_choice.side_effect = EOFError
        
        result = selection_box_tool(sample_holidays)
        
        assert result["status"] == "failure"
        assert "aborted" in result["message"]

def test_selection_box_tool_unexpected_exception(sample_holidays):
    """Test handling of unexpected errors."""
    with patch("tools.selection_box.selection_box_tool.choice") as mock_choice:
        mock_choice.side_effect = Exception("Terminal failure")
        
        result = selection_box_tool(sample_holidays)
        
        assert result["status"] == "failure"
        assert "unexpected error" in result["message"]
        assert "Terminal failure" in result["message"]
