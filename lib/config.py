import os
from dotenv import load_dotenv

load_dotenv()


def get_env_var(var_name, default_val=None):
    return os.getenv(var_name, default_val)
