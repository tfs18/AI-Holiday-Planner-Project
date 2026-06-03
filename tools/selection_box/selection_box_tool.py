from prompt_toolkit.shortcuts import choice
from typing import List, Dict, Any, Optional

def selection_box_tool(holidays_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Presents holiday destinations to the user via a CLI selection box and returns the choice.

    Args:
        holidays_list: A list of dictionaries containing holiday details.

    Returns:
        The selected holiday dictionary or None if cancelled.
    """
    if not holidays_list:
        print("No holiday destinations to display.")
        return None

    # Efficiently build the list of options for the choice box.
    # Each option is a tuple: (value_to_return, text_to_display)
    options = [
        (
            holiday,
            f"Destination: {holiday.get('city', 'Unknown')} | "
            f"Date: {holiday.get('date', 'N/A')} | "
            f"Score: {holiday.get('score', 0)}"
        )
        for holiday in holidays_list
    ]

    # Append a cancellation option that returns None.
    options.append((None, "I don't want to book anymore (Cancel)"))

    selected_holiday = choice(
        message="Please select a holiday destination to book:",
        options=options,
        default=0
    )

    if selected_holiday:
        print(f"You have chosen: {selected_holiday.get('city', 'Unknown')}")
    else:
        print("Selection cancelled.")

    return selected_holiday