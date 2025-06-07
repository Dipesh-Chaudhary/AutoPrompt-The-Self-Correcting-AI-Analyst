import streamlit as st
import textgrad as tg

@st.cache_resource
def get_generator_engine(name):
    """
    Retrieves a TextGrad engine instance for generation, with caching disabled.
    Args:
        name (str): The name or identifier of the TextGrad engine.
    Returns:
        An instance of the TextGrad engcacheine.
    """
    return tg.get_engine(name, cache=False)

@st.cache_resource
def get_evaluator_engine(name):
    """
    Retrieves a TextGrad engine instance for evaluation, with caching disabled.
    Args:
        name (str): The name or identifier of the TextGrad engine.
    Returns:
        An instance of the TextGrad engine.
    """
    return tg.get_engine(name, cache=False)

def handle_textgrad_exception(e, context="operation"):
    """
    Provides user-friendly error messages for common TextGrad exceptions.
    Args:
        e (Exception): The exception object.
        context (str): The context in which the error occurred (e.g., "table generation", "evaluation").
    """
    st.error(f"Error during {context}: {e}")
    print(f"Error during {context}: {e}")
    st.warning(
        "Please ensure API keys (e.g., GOOGLE_API_KEY) are correctly set in your environment "
        "and have access to the selected models. Also, verify the model names are correct."
    )
 