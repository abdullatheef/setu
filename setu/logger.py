import logging

# Create a logger
logger = logging.getLogger("setu")
logger.setLevel(logging.INFO)  # Set logging level

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Define log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add the handler to the logger (prevent duplicate handlers)
if not logger.handlers:
    logger.addHandler(console_handler)
