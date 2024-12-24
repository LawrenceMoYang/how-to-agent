import json
import os
if '/Users' not in os.path.expanduser("~"):
     os.environ['STREAMLIT_CACHE_DIR'] = "/shared-data"  # shared data path in the docker container
import streamlit as st
from src.docindex import DocIndex
from src.config import EMBEDDER_MODELS, CHAT_MODELS, SELLER_CONTENT_PATH, HELP_GUIDES_CONTENT_PATH
from src.generation import DialogueSystemGraph, load_llm


PROMPTS = {"Single Webpage Prompt":
               {"prompt_file": "single_webpage_output_list_prompt.txt", "top_k": 1},
           "Multiple Webpages Prompt":
               {"prompt_file": "multiple_webpages_prompt.txt", "top_k": 5}
           }

PROMPTS_PATH = "demos/demo_v0/prompts"


def show_page():
    st.title("How-to Agent")

    # Initialize chat history & reset button
    if st.sidebar.button("Reset Chat") or 'initialized' not in st.session_state:
        st.session_state.messages = []
        st.session_state.user_state = {'num_live_agent_calls': 0}
        st.session_state.initialized = True

    issues_sheet = "https://docs.google.com/spreadsheets/d/1gxN6K1FWv0hcjWdYnG6HOXDlKXvBOawR2nCBBghe2KE/edit?gid=322918608#gid=322918608"
    st.sidebar.markdown(f"[Report an issue]({issues_sheet})")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        model_selected = st.selectbox("Chat Model", options=CHAT_MODELS.keys(), index=1)
    with col2:
        prompt_selected = st.selectbox("Prompt", options=PROMPTS.keys(), index=1)
    with col3:
        embedder_selected = st.selectbox("Embedder Model", options=EMBEDDER_MODELS.keys(), index=1)
    with col4:
        max_tokens = st.selectbox("Max tokens", options=[512, 256, 1024])

    @st.cache_resource
    def get_doc_index(embedder_selected):
        doc_index = DocIndex(index_path=EMBEDDER_MODELS[embedder_selected]["index_path"],
                             embedder=EMBEDDER_MODELS[embedder_selected]["model_name"])

        if not os.path.exists(EMBEDDER_MODELS[embedder_selected]["index_path"]):
            doc_index.build(index_path=EMBEDDER_MODELS[embedder_selected]["index_path"],
                            content_paths=[SELLER_CONTENT_PATH, HELP_GUIDES_CONTENT_PATH],
                            embedder_model_name=EMBEDDER_MODELS[embedder_selected]["model_name"],
                            chunk_size=EMBEDDER_MODELS[embedder_selected]["chunk_size"])
        return doc_index

    @st.cache_resource
    def get_conversation(model, max_tokens, temperature):
        return load_llm(model, max_tokens, temperature)

    @st.cache_resource
    def get_answerer(
            _index,
            intent_file,
            prompt_file,
            no_intent_answer_file,
            live_agent_answer_file,
            no_response_answer_file
    ):
        return DialogueSystemGraph(
            index=_index,
            prompt_file_intent=intent_file,
            prompt_file_answerer=prompt_file,
            no_intent_answer_file=no_intent_answer_file,
            live_agent_answer_file=live_agent_answer_file,
            no_response_answer_file=no_response_answer_file,
        )

    llm = get_conversation(CHAT_MODELS[model_selected], max_tokens, 0.0)

    index = get_doc_index(embedder_selected)

    answerer = get_answerer(
        index,
        os.path.join(PROMPTS_PATH, "dialogue_system_input_prompt.txt"),
        os.path.join(PROMPTS_PATH, "rag_probing_prompt.txt"),
        os.path.join(PROMPTS_PATH, "no_intent_response.txt"),
        os.path.join(PROMPTS_PATH, "live_agent_response.txt"),
        os.path.join(PROMPTS_PATH, "no_answer_response.txt"),
    )

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    meta_info = {}

    if question := st.chat_input("How to boost my selling?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(question)
        # Add user message to chat history
        print(st.session_state.user_state)
        st.session_state.messages.append({"role": "user", "content": question})
        response, meta_info = answerer.answer_question(
            messages=st.session_state.messages,
            llm=llm,
            top_k=PROMPTS[prompt_selected]['top_k'],
            user_context=st.session_state.user_state,
        )

        with st.chat_message("assistant"):
            st.markdown(response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

    st.sidebar.json(meta_info)


if __name__ == "__main__":
    if "auth_tokens" not in st.session_state:
        st.session_state.auth_tokens = None

    if not st.session_state.auth_tokens:
        st.session_state.redirect_page = "pages/20_agent_with_intent.py"
        st.switch_page("main_app.py")
    else:
        show_page()