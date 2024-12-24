import json
from pychomsky.chchat import EbayLLMChatWrapper
import random
import time


llm = EbayLLMChatWrapper(
        model_name="openai-chat-completions-gpt-4o-mini-2024-07-18",
        temperature=0.5,
        max_tokens=2048
    )

def retry_with_backoff(
    func,
    args=None,
    kwargs=None,
    max_retries=3,
    base_sleep=2,
    exceptions=(Exception,),
    skip_retry_exceptions=(json.JSONDecodeError,),
):
    """
    A generic retry mechanism with exponential backoff and jitter.

    Args:
        func (callable): The function to retry.
        args (tuple): Positional arguments to pass to the function.
        kwargs (dict): Keyword arguments to pass to the function.
        max_retries (int): Maximum number of retries.
        base_sleep (int): Base sleep time for exponential backoff.
        exceptions (tuple): Tuple of exception types to retry on.

    Returns:
        Any: The result of the function if it succeeds.

    Raises:
        Exception: The last exception if all retries fail.
    """
    args = args or ()
    kwargs = kwargs or {}
    retries = 0

    while retries <= max_retries:
        try:
            # Attempt the function call
            return func(*args, **kwargs)
        except skip_retry_exceptions as e:
            retries += 1
            if retries > max_retries:
                return None
        except exceptions as e:
            retries += 1
            if retries > max_retries:
                return None
            
            sleep_time = base_sleep * retries
            print(f"Retrying ({retries}/{max_retries}) after {sleep_time:.2f} seconds due to: The request limit has been reached for the resource")
            time.sleep(sleep_time)


def generate_questions(prompt, text):
    """
    Generate questions using an LLM call.
    """
    formatted_prompt = prompt.replace("{{text}}", text)
    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates questions."},
        {"role": "user", "content": formatted_prompt}
    ]

    # Define the function to call the LLM
    def llm_call():
        response = llm.invoke(messages)  # Replace `llm.invoke` with your actual API call
        return extract_json(response.content)

    # Use the generic retry mechanism
    return retry_with_backoff(
        llm_call,
        max_retries=5,
        base_sleep=10,
        exceptions=(Exception,),
        skip_retry_exceptions=(json.JSONDecodeError,)
    )
                              

def extract_json(content):
    """
    Extracts and parses JSON data from the response content.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as jde:
        print(jde)
        # Raise JSONDecodeError for proper exception handling
        raise json.JSONDecodeError(msg=str(jde), doc=content, pos=0)
    except Exception as e:
        print(e)
        # Wrap other exceptions as JSONDecodeError for consistency
        raise json.JSONDecodeError(msg=f"Unexpected error: {e}", doc=content, pos=0)