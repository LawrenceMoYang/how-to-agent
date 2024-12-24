import json

from langchain_core.messages import HumanMessage
from pychomsky.chchat import AzureOpenAIChatWrapper, EbayLLMChatWrapper


_LIVE_AGENT_CALLS_THRESH = 2


def conversation_from_messages(messages: list) -> str:
    conversation = ""

    for message in messages:
        conversation += message['role'].upper() + ':\n'
        conversation += message['content'] + '\n\n'
    return conversation


def parse_json_safely(json_string: str) -> dict | None:
    start_index = json_string.find('{')
    end_index = json_string.rfind('}')
    parsed_json_string = json_string[start_index:end_index + 1]
    try:
        predicted_json = json.loads(parsed_json_string)
    except json.JSONDecodeError:
        print('JSON parsing failed')
        print(parsed_json_string)
        predicted_json = None
    return predicted_json


def format_answer_from_json(json_response, default_link="https://www.ebay.com/help/home") -> str:
    """
    Parse the JSON response to create a human-readable answer string.
    Returns the answer and source URL if available, or the support link if no answer is found.
    """
    try:
        json_response = json_response.strip(' ```json\n').strip('\n```')  # Remove code block markdown for Phi3.5
        response_data = json.loads(json_response)

        # Check if the JSON contains an answer
        if response_data.get("answer") and response_data.get("source"):
            sources = "\n".join([f"- {source}" for source in set(response_data['source'])])
            answer_string = f"{response_data['answer']}\n\nFor more information please visit:\n{sources}"
            return answer_string
        else:
            # Return the support link if no answer is found
            return f"Please go to {default_link} to get support."
    except json.JSONDecodeError:
        # Handle cases where the output is not valid JSON (if any)
        return f"Please go to {default_link} to get support."


class Answerer:
    def __init__(self, index, prompt_file):
        self.index = index
        # Load the prompt template from the file
        with open(prompt_file, 'r') as file:
            self.prompt_template = file.read()

    def get_raw_response(self, messages: list[dict], llm: AzureOpenAIChatWrapper, top_k: int, query: str | None = None):
        # Perform the search to retrieve relevant paragraphs
        assert messages and messages[-1]['role'] == 'user'
        if not query:
            query = messages[-1]['content']

        search_results = self.index.search_full(query, top_k)

        # Change for the future when we'll have more metadata in the index
        combined_paragraphs_webpages = "\n".join(
            [f"Paragraph {i + 1}:\n{res['chunk']}\nSource {i + 1}:\n{res['url']}\n" for i, res in
             enumerate(search_results)])

        conversation = conversation_from_messages(messages)

        # Format the prompt with the retrieved data and the question
        prompt = self.prompt_template.format(paragraphs=combined_paragraphs_webpages, messages=conversation)
        print(f"Prompt: \n{prompt}")

        # Get the JSON response from the conversation chain
        json_response = llm.invoke([HumanMessage(content=prompt)])
        print(f"JSON Response: \n{json_response.content}")
        return json_response

    def answer_question(self, messages: list[dict], llm: AzureOpenAIChatWrapper, top_k: int, query: str | None = None):
        json_response = self.get_raw_response(messages, llm, top_k, query)

        assistant_response = format_answer_from_json(json_response.content)

        return assistant_response


class DialogueSystemGraph:
    def __init__(
            self,
            index,
            prompt_file_intent,
            prompt_file_answerer,
            no_intent_answer_file,
            live_agent_answer_file,
            no_response_answer_file,
    ):
        self.answerer = Answerer(index, prompt_file_answerer)
        with open(prompt_file_intent, 'r') as file:
            self.intent_prompt = file.read()

        with open(no_intent_answer_file, 'r') as file:
            self.no_intent_answer_file = file.read()

        with open(live_agent_answer_file, 'r') as file:
            self.live_agent_answer = file.read()

        with open(no_response_answer_file, 'r') as file:
            self.no_response_answer = file.read()

    def answer_question(self, messages: list[dict], llm: AzureOpenAIChatWrapper, top_k: int, user_context: dict):
        assert messages and messages[-1]['role'] == 'user'

        conversation = conversation_from_messages(messages)

        # Format the prompt with the retrieved data and the question
        prompt = self.intent_prompt.format(messages=conversation)
        print(f"Intent prompt: \n{prompt}")

        json_response = llm.invoke([HumanMessage(content=prompt)])
        print(f"Intent Response: \n{json_response.content}")

        intent_response = parse_json_safely(json_response.content)

        assert intent_response

        query = intent_response.get('query', None)
        clarity = intent_response.get('clarity', 10)
        missing_details = intent_response.get('missing_details', [])
        no_search = intent_response.get('no_search', None)
        user = intent_response.get('user', None)
        live_agent = intent_response.get('live_agent', None)

        if no_search and not live_agent:
            # It's not something we can answer
            return self.no_intent_answer_file, intent_response

        assistant_response = ''

        if not no_search:
            # We need to fetch the RAG response
            call_llm = self.answerer.get_raw_response(messages, llm, top_k, query)
            rag_response = parse_json_safely(call_llm.content)

            response_type = rag_response['case']

            if response_type == 'Clear answer':
                sources = "\n".join([f"- {source}" for source in set(rag_response['source'])])
                answer_string = f"{rag_response['answer']}\n\nFor more information please visit:\n{sources}"
                assistant_response += answer_string

            elif response_type == 'Ambiguity':
                sources = "\n".join([f"- {source}" for source in set(rag_response['source'])])
                answer_string = f"{rag_response['question']}\n\nFor more information please visit:\n{sources}"
                assistant_response += answer_string

            else:
                assistant_response += self.no_response_answer

        if live_agent:
            # Live agent was requested
            user_context['num_live_agent_calls'] += 1
            if user_context['num_live_agent_calls'] >= _LIVE_AGENT_CALLS_THRESH or no_search:
                # We need to add the info about contacting support
                assistant_response += '\n\n\n' + self.live_agent_answer

        else:
            user_context['num_live_agent_calls'] = 0

        # if clarity < 8 and missing_details:
        #     assistant_response += f"\n\nPlease provide the following info:"
        #     for question in missing_details:
        #         assistant_response += f'\n- {question}'

        return assistant_response, intent_response


def load_llm(model: str, max_tokens: int, temperature: float) -> AzureOpenAIChatWrapper:
    llm = EbayLLMChatWrapper(model_name=model, max_tokens=max_tokens, temperature=temperature)

    return llm
