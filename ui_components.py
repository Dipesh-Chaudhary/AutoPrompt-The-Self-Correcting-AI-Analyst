import streamlit as st
import pandas as pd
import io

def display_text_with_copy_and_download(label, text_content, height=200, key_suffix="", disabled=True, help_text=None, filename="downloaded_text.txt"):
    """
    Displays text in a text_area with a copy hint and a download button.
    Args:
        label (str): The label for the text area.
        text_content (str): The text to display.
        height (int): Height of the text area.
        key_suffix (str): Unique suffix for widget keys.
        disabled (bool): Whether the text area should be disabled (read-only).
        help_text (str, optional): Help tooltip for the text area.
        filename (str): Default filename for downloaded text.
    """
    st.text_area(
        label,
        value=str(text_content) if text_content is not None else "", # Ensure text_content is a string
        height=height,
        key=f"text_display_{key_suffix}",
        disabled=disabled,
        help=help_text if help_text else "Select text and press Ctrl+C (or Cmd+C) to copy."
    )
    
    # Only show buttons if there is content
    if text_content:
        col1, col2 = st.columns([0.6, 0.4]) # Adjust column ratios as needed
        with col1:
            # The "copy hint" button might be less necessary if the text_area help text is clear.
            # For simplicity, let's focus on the download. Users know how to select and copy.
            pass # st.button(f"📋 Hint: Select & Copy {label.lower()}", key=f"copy_hint_button_{key_suffix}")
                 # if st.button(...): st.toast(...)
        
        # Ensure download button is always available if content exists
        # It was in col2 before, let's make it more prominent or ensure it's always rendered.
        st.download_button(
            label=f"💾 Download {label.lower()}",
            data=str(text_content).encode('utf-8') if text_content else "".encode('utf-8'),
            file_name=filename,
            mime="text/plain",
            key=f"download_text_{key_suffix}"
        )
    else:
        st.caption(f"{label} is empty.")


def view_edit_prompt_ui(label, prompt_text_state_key, mode_state_key, key_prefix, filename_base="prompt"):
    """
    Creates an expandable UI block for viewing or editing a prompt.
    Includes download button for the prompt.
    Args:
        label (str): The label for the expander.
        prompt_text_state_key (str): Session state key for the prompt text.
        mode_state_key (str): Session state key for the view/edit mode.
        key_prefix (str): Unique prefix for widget keys.
        filename_base (str): Base name for the downloaded prompt file.
    """
    with st.expander(label):
        if mode_state_key not in st.session_state:
            st.session_state[mode_state_key] = 'view'

        cols_mode_select = st.columns([1, 3])
        current_mode_selection = cols_mode_select[0].radio(
            "Mode", ['View', 'Edit'],
            key=f'{key_prefix}_mode_radio',
            index=0 if st.session_state[mode_state_key] == 'view' else 1,
            label_visibility="collapsed"
        )
        st.session_state[mode_state_key] = current_mode_selection.lower()

        content_container_style = """
            background-color: rgba(230, 247, 255, 0.5);
            padding: 15px; border-radius: 8px;
            border: 1px solid rgba(173, 216, 230, 0.8); margin-top: 10px;
        """
        st.markdown(f'<div style="{content_container_style}">', unsafe_allow_html=True)

        prompt_content = st.session_state.get(prompt_text_state_key, "") # Ensure key exists

        if st.session_state[mode_state_key] == 'view':
            st.markdown("##### Prompt Content (View Mode)")
            st.text_area(
                "Prompt Text (Read-Only)", prompt_content,
                height=300, key=f'{key_prefix}_view_textarea', disabled=True,
                help="Select text and press Ctrl+C (or Cmd+C) to copy."
            )
        elif st.session_state[mode_state_key] == 'edit':
            st.markdown("##### Prompt Content (Edit Mode)")
            edited_text = st.text_area(
                "Edit Prompt Here:", prompt_content,
                height=400, key=f'{key_prefix}_edit_textarea'
            )
            if st.button("💾 Confirm Changes", key=f'{key_prefix}_confirm_button'):
                st.session_state[prompt_text_state_key] = edited_text
                st.success("Prompt changes confirmed and updated for the current session.")
        
        # Download button available in both modes, only if prompt_content exists
        if prompt_content:
            st.download_button(
                label=f"💾 Download this Prompt as .txt",
                data=str(prompt_content).encode('utf-8'),
                file_name=f"{filename_base}_{key_prefix}.txt",
                mime="text/plain",
                key=f'{key_prefix}_download_button'
            )
        else:
            st.caption("Prompt content is empty.")
            
        st.markdown('</div>', unsafe_allow_html=True)


def display_df_with_download_and_copy(df, table_text, filename_prefix="table_report", key_suffix=""):
    """
    Displays a Pandas DataFrame, offers a download button for CSV, and download for raw text.
    """
    st.dataframe(df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=f"📥 Download Table as CSV (TAB)",
            data=str(table_text).encode('utf-8') if table_text else "".encode('utf-8'),
            file_name=f"{filename_prefix}_{key_suffix}.csv", # technically .tsv but .csv is common
            mime="text/tab-separated-values", # More accurate mime type
            key=f"download_csv_{key_suffix}"
        )
    with col2:
        st.download_button(
            label=f"💾 Download Raw Table Text",
            data=str(table_text).encode('utf-8') if table_text else "".encode('utf-8'),
            file_name=f"{filename_prefix}_raw_{key_suffix}.txt",
            mime="text/plain",
            key=f"download_raw_table_txt_{key_suffix}"
        )

def render_understanding_optimization_section():
    """Renders the explanation section about TextGrad optimization."""
    st.header("6. Understanding Optimization")
    st.write("""
    TextGrad's optimization uses a form of *textual* gradient descent. It leverages an Evaluator LLM to:
    1. Analyze the generated output against the evaluation criteria.
    2. Provide textual feedback (the "gradient") on how the *input system prompt* should be improved.
    3. The Textual Gradient Descent (TGD) optimizer interprets this feedback and modifies the prompt text.

    **Why the Score Might Fluctuate (and the Importance of History):**
    * **LLM Stochasticity:** Language models aren't fully deterministic. The Generator and Evaluator might produce slightly different results even with the same inputs, causing score variations.
    * **Evaluation Nuance:** The Evaluator LLM's scoring and feedback might have slight inconsistencies.
    * **Textual Interpretation:** The TGD optimizer's process of modifying text based on feedback is heuristic, not a mathematically precise step towards a guaranteed optimum.
    * **Exploring the Prompt Space:** The optimizer might explore prompt variations that temporarily decrease the score before finding a better direction.

    **How This App Handles It:**
    * **Tracking the Best:** The app always saves the prompt that achieved the **highest score** during the optimization run (shown in Section 4). This ensures you don't lose the best result found. You can download this best prompt and also save it to your local library.
    * **Viewing History:** The **Optimization History** (Section 5) allows you to see the prompt, score, and feedback for each step. This helps understand the optimization path. You can download prompts from history.
    * **Prompt Library (New Feature):** In Section 1, you can load prompts from your saved library. In Section 4 (Best Optimization Result), there's an option to "Save this Best Prompt to Library".
    * **Continuing Optimization:** The editable prompt (in Section 3) is updated to the *final state* after the optimization loop finishes.
    """)