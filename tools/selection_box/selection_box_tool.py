from prompt_toolkit.shortcuts import choice
from typing import List, Dict, Any

def selection_box_tool(holidays_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Presents holiday destinations to the user via a CLI selection box and returns the choice.

    The holidays_list parameter should be a list of dictionaries with the following keys:
    - 'ranking': int or str (e.g., 1)
    - 'city': str (e.g., 'Paris')
    - 'date': str (e.g., '2026-06-15')
    - 'weather': str (e.g., 'Sunny')
    - 'score': float or int (e.g., 85.5)

    Args:
        holidays_list: A list of dictionaries containing holiday details.

    Returns:
        A dictionary containing:
        - status: "success" (if a choice was made), "failure" (if cancelled or error).
        - data: The selected holiday dictionary (if success).
        - message: Error or cancellation description (if failure).
    """
    # 1. Input Validation
    if not holidays_list:
        return {
            "status": "failure",
            "message": "No holiday destinations provided."
        }

    valid_holidays = []
    for item in holidays_list:
        if isinstance(item, dict):
            valid_holidays.append(item)
        else:
            # Skip invalid items or we could return an error
            continue

    if not valid_holidays:
        return {
            "status": "failure",
            "message": "Input validation error: No valid holiday dictionaries found in list."
        }

    # 2. Build options for the choice box
    options = [
        (
            holiday,
            f"Location: {holiday.get('city', 'Unknown')} | "
            f"Date: {holiday.get('date', 'N/A')} | "
            f"Weather: {holiday.get('weather', 'N/A')} | "
            f"Score: {holiday.get('score', 0)}"
        )
        for holiday in valid_holidays
    ]

    # Append a cancellation option that returns None.
    # We use a unique object or check against None to distinguish from empty dicts
    options.append((None, "I don't want to book anymore (Cancel)"))

    try:
        # 3. Present choice box
        selected_holiday = choice(
            message="Please select a holiday destination to book:",
            options=options,
            default=0
        )

        # Handle cancellation (User picked "None" option)
        if selected_holiday is None:
            print("Selection cancelled.")
            return {
                "status": "failure",
                "message": "user cancelled operation"
            }

        # Success case
        print(f"You have chosen: {selected_holiday.get('city', 'Unknown')}")
        return {
            "status": "success",
            "data": selected_holiday
        }

    except (KeyboardInterrupt, EOFError):
        # Handle Ctrl+C or Ctrl+D gracefully
        print("\nSelection aborted.")
        return {
            "status": "failure",
            "message": "user aborted selection (Ctrl+C/Ctrl+D)"
        }
    except Exception as e:
        # Catch-all for any other prompt_toolkit or terminal errors
        return {
            "status": "failure",
            "message": f"An unexpected error occurred during selection: {str(e)}"
        }