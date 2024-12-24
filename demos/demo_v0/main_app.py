import os
import sys
from time import sleep

import streamlit as st

from utils.utils import fetch_proxies, is_production_connected, fetch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
sys.path.append(os.path.join(os.path.dirname(__file__), project_root + '/src'))

# Custom CSS for styling
base_ui_css = """
    <style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f9f9f9;
        color: #333;
        margin: 0;
        padding: 0;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    }
    h1, h2 {
        font-weight: bold;
        color: #1a1a1a; /* Dark Gray */
    }
    h1 {
        font-size: 36px;
        margin-bottom: 20px;
    }
    h2 {
        font-size: 24px;
        margin-bottom: 20px;
    }
    .sidebar .sidebar-content {
        padding: 20px;
    }
    </style>
    """


# Main Streamlit App
def main():
    st.set_page_config(layout="wide")
    st.markdown(base_ui_css, unsafe_allow_html=True)

    if "auth_tokens" not in st.session_state or st.session_state.auth_tokens is None:
        st.markdown("<h1 class='login-title'>Please Login</h1>", unsafe_allow_html=True)

        proxy_username = st.text_input("Username", value="")
        proxy_pin_and_yubikey = st.text_input("PIN + TAP YUBIKEY:", value="", type="password")

        if st.button('Authorize'):
            successed = is_production_connected(
                proxies=fetch_proxies(yubi_user=proxy_username, yubi_key=proxy_pin_and_yubikey))

            if successed:
                bearer_token = fetch(proxy_username, proxy_pin_and_yubikey,
                                     url="https://recenrichmentsvc.vip.ebay.com/rec/api/v1/authentication/token").text
                proxy_username = proxy_username
                proxy_pin_and_yubikey = proxy_pin_and_yubikey

                st.session_state.auth_tokens = {
                    "yubi_user": proxy_username,
                    "yubi_key": proxy_pin_and_yubikey,
                    "bearer_token": bearer_token
                }

                st.success("Authorized successfully!")
                sleep(1.0)
                if 'redirect_page' in st.session_state and st.session_state.redirect_page is not None:
                    redirect_page = st.session_state.redirect_page
                    del st.session_state.redirect_page
                    st.switch_page(redirect_page)
                else:
                    st.switch_page("pages/10_agent_page.py")
            else:
                st.error("Authorization failed! Please check your credentials and try again.")


if __name__ == "__main__":
    main()
