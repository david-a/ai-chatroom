from openai import OpenAI
import tiktoken
from lib.config import get_env_var
from lib.utils import deserialize_message

OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")

MODEL_NAME = "gpt-3.5-turbo-0613"
MODEL_MAX_INPUT_TOKENS = 4096
MAX_TOKENS_TO_GENERATE = 100
MODEL_TEMPERATURE = 0.7

client = None


def get_openai_client():
    global client
    if client is None:
        client = OpenAI(
            api_key=OPENAI_API_KEY,
        )
    return client


def wrap_system_message(text):
    return {
        "role": "system",
        "content": " ".join(text.split()),
    }


def to_openai_message(msg, self_name):
    sender, content = deserialize_message(msg)
    m = {
        "role": "assistant" if sender == self_name else "user",
        "content": content,
        "name": sender,
    }
    return m


# NOTE: Calculation based on "gpt-3.5-turbo-0613"- future models may deviate from this
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    num_tokens = 0
    for message in messages:
        num_tokens += (
            4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        )
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def limit_tokens(messages, system_message, max_tokens):
    """Limits the number of tokens used by a list of messages."""
    full_prompt = [system_message, *messages]
    if num_tokens_from_messages(full_prompt) <= max_tokens:
        return messages
    else:
        return limit_tokens(messages[1:], system_message, max_tokens)


def ai_call(conversation, system_prompt, bot_name="AI"):
    """
    This function makes a call to the AI model to generate a response based on the provided conversation.

    Parameters:
    conversation (list): A list of conversation messages to be processed by the AI. Each message is a string in the format "sender: message".
    system_prompt (str): The system prompt to be used for the AI model.


    Returns:
    str: The content of the AI model's response.

    """
    # print(
    #     "\n\nDEBUG: ai_call - CONVERSATION and SYSTEM PROMPT: \n\n",
    #     conversation,
    #     system_prompt,
    # )
    system_message = wrap_system_message(system_prompt)

    capped_messages = limit_tokens(
        list(map(lambda msg: to_openai_message(msg, bot_name), conversation)),
        system_message,
        MODEL_MAX_INPUT_TOKENS,
    )

    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[system_message, *capped_messages],
            temperature=MODEL_TEMPERATURE,
            max_tokens=MAX_TOKENS_TO_GENERATE,
        )
    except Exception as e:
        print("ai_call: Error calling OpenAI: ", e)
        return "I had something to say but encountered a technical issue."
    return response.choices[0].message.content
