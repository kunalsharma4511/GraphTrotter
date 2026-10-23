import os

# Set before the app code loads your .env; load_dotenv() does not override existing values.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"