from google import genai
from dotenv import load_dotenv
import os
from logs.logging_config import setup_logging
import logging
from functions.cli_loop import cli_loop

load_dotenv()

setup_logging()

#This is how to get the right logging instance.
logger = logging.getLogger("holiday-agent")

logger.info("App started")


def main():
    cli_loop()



if __name__ == "__main__":
    main()