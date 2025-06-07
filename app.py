import csv
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import textgrad as tg
from datetime import datetime
import pandas as pd
import io
import os
# import re # Not directly used here if parse_evaluation_output is solely in utils

# --- Import from local modules ---
from config import (
    AVAILABLE_MODELS, INITIAL_SYSTEM_PROMPT_TEXT,
    USER_QUERY_TEMPLATE, EVALUATION_PROMPT_TEMPLATE
)
from textgrad_utils import (
    get_generator_engine, get_evaluator_engine, handle_textgrad_exception
)
from ui_components import (
    view_edit_prompt_ui, display_df_with_download_and_copy,
    display_text_with_copy_and_download, 
    render_understanding_optimization_section
)
from utils import ( 
    parse_evaluation_output, save_prompt_to_library,
    load_prompt_from_library, get_saved_prompts_list,
    ensure_saved_prompts_dir # Ensure this is called early if needed
)

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="TextGrad Report Optimizer")

# --- Ensure saved_prompts directory exists on app start ---
ensure_saved_prompts_dir()

# --- Session State Initialization ---
def initialize_session_state():
    defaults = {
        'app_step': 0,
        'current_system_prompt_text': INITIAL_SYSTEM_PROMPT_TEXT,
        'system_prompt_mode': 'view',
        'evaluation_prompt_template_text': EVALUATION_PROMPT_TEMPLATE,
        'eval_prompt_mode': 'view',
        'generator_llm_name': "Gemini 1.5 Flash", # Default, ensure it's in AVAILABLE_MODELS
        'evaluator_llm_name': "Gemini 2.5 Flash Preview", 
        'user_input_data': {},
        'external_data_provided': False,
        'formatted_user_prompt_text': "",
        'formatted_user_prompt_var': None,
        'learnable_system_prompt_var': None,
        'last_generated_table_text': "",
        'last_generated_table_variable': None,
        'generated_prompt_for_eval': "",
        'last_evaluation_output': "",
        'last_loss_object': None,
        'last_evaluation_score': None,
        'last_evaluation_description': "",
        'last_evaluation_feedback': "",
        'loss_instruction_var': None,
        'loss_fn': None,
        'best_optimized_system_prompt_text': "",
        'best_optimized_table_text': "",
        'best_optimized_score': None,
        'best_optimized_description': "",
        'best_optimized_feedback': "",
        'best_optimized_step': -1,
        'num_opt_steps': 3,
        'target_score_thresh': 90,
        'optimization_history': [],
        'prompt_library_selector_key': 0, # Used to force re-render of selectbox if list changes
        'selected_prompt_from_library_name': "Use Initial Default Prompt", # Initial state for dropdown
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Ensure default LLM names are valid
    if st.session_state.generator_llm_name not in AVAILABLE_MODELS:
        st.session_state.generator_llm_name = list(AVAILABLE_MODELS.keys())[0]
    if st.session_state.evaluator_llm_name not in AVAILABLE_MODELS:
        # Try to pick a different one from generator if possible, or first one
        gen_idx = list(AVAILABLE_MODELS.keys()).index(st.session_state.generator_llm_name)
        eval_idx = (gen_idx + 1) % len(AVAILABLE_MODELS) if len(AVAILABLE_MODELS) > 1 else 0
        st.session_state.evaluator_llm_name = list(AVAILABLE_MODELS.keys())[eval_idx]


initialize_session_state()

# --- Helper: Display Table ---


def try_display_table(table_text, key_suffix="display", download_filename="generated_report"):
    if not table_text or not isinstance(table_text, str): # Added check for isinstance
        st.info("No table content to display.")
        return

    try:
        lines = table_text.strip().split('\n')
        header_index = 0
        # More robust header detection: find the line that *starts* with "Strategic Imperative" or similar
        # and contains multiple tab characters, suggesting it's a header row.
        for i, line in enumerate(lines):
            # Check if the line starts with a known header and has tabs (likely a TSV header)
            if line.strip().lower().startswith('"strategic imperative"') and '\t' in line:
                header_index = i
                break
            # Fallback for slightly different quoting, if necessary
            elif line.strip().lower().startswith('strategic imperative') and '\t' in line:
                 header_index = i
                 break
        
        processed_table_text = "\n".join(lines[header_index:])

        table_io = io.StringIO(processed_table_text)

        df = pd.read_csv(table_io, sep='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL, keep_default_na=False, dtype=str, skipinitialspace=True)
        
        # Check if DataFrame is empty or has only headers after processing
        if df.empty and processed_table_text.strip():
             st.warning("Could not parse table into DataFrame structure. Displaying raw text. Please check TSV format and quoting.")
             display_text_with_copy_and_download(
                label="Raw Table Content (Parsing Failed)",
                text_content=table_text, # Show original text if parsing failed
                height=300,
                key_suffix=f"raw_table_parse_fail_{key_suffix}",
                filename=f"{download_filename}_raw_parsing_failed.txt"
            )
        elif df.empty:
            st.info("Table content appears empty after processing.")
        else:
            display_df_with_download_and_copy(df, table_text, filename_prefix=download_filename, key_suffix=key_suffix)
    except Exception as e:
        st.warning(f"Could not display table as DataFrame: {e}. Displaying raw text.")
        display_text_with_copy_and_download(
            label="Raw Table Content (Error)",
            text_content=table_text,
            height=300,
            key_suffix=f"raw_table_error_{key_suffix}",
            filename=f"{download_filename}_raw_error.txt"
        )
# --- Sidebar: User Inputs (Remains the same as your last version) ---
with st.sidebar:
    st.header("0. Define User Inputs")
    st.subheader("Mandatory Fields")
    user_input_data = st.session_state.user_input_data 

    user_input_data["industry"] = st.text_input("Industry", value=user_input_data.get("industry", "mobility"), key='industry_input')
    user_input_data["region"] = st.text_input("Region", value=user_input_data.get("region", "middle east"), key='region_input')
    user_input_data["transformational_journey"] = st.text_input("Transformational Journey", value=user_input_data.get("transformational_journey", "shared mobility"), key='transformational_journey_input')
    user_input_data["program_area"] = st.text_input("Program Area", value=user_input_data.get("program_area", "ride hailing"), key='program_area_input')

    st.subheader("Optional Fields")
    user_input_data["company_name"] = st.text_input("Company Name", value=user_input_data.get("company_name", "NOT PROVIDED"), key='company_name_input')
    user_input_data["future_year"] = st.number_input("Future Years from Current", min_value=1, value=user_input_data.get("future_year", 20), format="%d", key='future_year_input')
    user_input_data["unrelated_keywords"] = st.text_input("Unrelated Keywords", value=user_input_data.get("unrelated_keywords", ""), key='unrelated_keywords_input')

    st.subheader("External Data Inputs (Paste Here - At least one required)")
    external_data_keys = ["google_agent_output", "bard_outputs", "web_content", "url_output", "gnews_output"]
    external_data_provided_flag = False
    for key in external_data_keys:
        user_input_data[key] = st.text_area(key.replace("_", " ").title(), value=user_input_data.get(key, ""), height=100, key=f'{key}_input')
        if user_input_data[key] and user_input_data[key].strip(): # Check if not None and not empty string
            external_data_provided_flag = True

    st.session_state.user_input_data = user_input_data
    st.session_state.external_data_provided = external_data_provided_flag

# --- Main Application ---
st.title(" Table Report Generator & Optimizer Using ---**TextGrad**---")

# --- LLM Engine Selection (Remains the same as your last version) ---
st.markdown("---")
st.header("LLM Engine Selection")
col_gen, col_eval = st.columns(2)
with col_gen:
    # Ensure index is valid
    gen_llm_keys = list(AVAILABLE_MODELS.keys())
    try:
        gen_default_index = gen_llm_keys.index(st.session_state.generator_llm_name)
    except ValueError:
        gen_default_index = 0 # Fallback to first model
        st.session_state.generator_llm_name = gen_llm_keys[gen_default_index]

    selected_generator_llm_key = st.selectbox(
        "Select Generator LLM", gen_llm_keys,
        index=gen_default_index,
        key='generator_llm_select',
        help="Choose the LLM for generating table reports."
    )
    st.session_state.generator_llm_name = selected_generator_llm_key
    llm_engine = get_generator_engine(AVAILABLE_MODELS[selected_generator_llm_key])

with col_eval:
    eval_llm_keys = list(AVAILABLE_MODELS.keys())
    try:
        eval_default_index = eval_llm_keys.index(st.session_state.evaluator_llm_name)
    except ValueError:
        eval_default_index = 0 # Fallback
        st.session_state.evaluator_llm_name = eval_llm_keys[eval_default_index]

    selected_evaluator_llm_key = st.selectbox(
        "Select Evaluator LLM", eval_llm_keys,
        index=eval_default_index,
        key='evaluator_llm_select',
        help="Choose the LLM for evaluating generated tables and providing feedback for optimization."
    )
    st.session_state.evaluator_llm_name = selected_evaluator_llm_key
    # Configure evaluator engine, potentially with model_kwargs for temperature
    # This is conceptual, actual TextGrad API for model_kwargs might differ
    # evaluator_model_kwargs = {"temperature": 0.1} # Example
    # llm_evaluator = get_evaluator_engine(AVAILABLE_MODELS[selected_evaluator_llm_key], model_kwargs=evaluator_model_kwargs)
    llm_evaluator = get_evaluator_engine(AVAILABLE_MODELS[selected_evaluator_llm_key]) # Simpler for now
    # llm_evaluator = tg.get_engine(AVAILABLE_MODELS[selected_evaluator_llm_key],cache=False) # Simpler for now
    tg.set_backward_engine(llm_evaluator, override=True)

    

st.markdown("---")

# --- Section 1: Initial Table Generation (WITH PROMPT LIBRARY) ---
st.header("1. Initial Table Generation")

st.subheader("Load or Define System Prompt") # <-- SUBHEADER FOR THIS SECTION
saved_prompts_files = get_saved_prompts_list() 
prompt_options_map = {"Use Initial Default Prompt": INITIAL_SYSTEM_PROMPT_TEXT, 
                      "Use Current Editor Content": st.session_state.current_system_prompt_text}
display_options = ["Use Initial Default Prompt", "Use Current Editor Content"]

if saved_prompts_files:
    display_options.append("----- Saved Prompts -----")
    for fname in saved_prompts_files: # saved_prompts_files contains filenames like "my_prompt.txt"
        display_options.append(fname) 

# Determine default index for selectbox
current_selected_option_in_ss = st.session_state.selected_prompt_from_library_name
if current_selected_option_in_ss in display_options:
    default_index_selectbox = display_options.index(current_selected_option_in_ss)
else: 
    st.session_state.selected_prompt_from_library_name = "Use Current Editor Content"
    default_index_selectbox = display_options.index("Use Current Editor Content")


def on_prompt_selection_change():
    selected_option = st.session_state.prompt_library_selector_actual 
    st.session_state.selected_prompt_from_library_name = selected_option 

    if selected_option == "Use Initial Default Prompt":
        st.session_state.current_system_prompt_text = INITIAL_SYSTEM_PROMPT_TEXT
        st.toast("Loaded Initial Default Prompt into editor.")
    elif selected_option == "Use Current Editor Content":
        st.toast("Editor content remains active.")
    elif selected_option and selected_option not in ["----- Saved Prompts -----"]:
        # A specific saved prompt filename was selected
        loaded_prompt = load_prompt_from_library(selected_option) # 'selected_option' is the filename
        if loaded_prompt is not None:
            st.session_state.current_system_prompt_text = loaded_prompt
            st.toast(f"Loaded '{selected_option}' into editor.")
        else:
            st.error(f"Failed to load '{selected_option}'. Reverting to editor content.")
            # Fallback logic if needed, e.g., revert to INITIAL_SYSTEM_PROMPT_TEXT
            st.session_state.current_system_prompt_text = st.session_state.get('current_system_prompt_text_backup', INITIAL_SYSTEM_PROMPT_TEXT) 
            st.session_state.selected_prompt_from_library_name = "Use Current Editor Content"
    # Backup current prompt before changing, useful for editor stability
    st.session_state.current_system_prompt_text_backup = st.session_state.current_system_prompt_text


selected_prompt_source_actual = st.selectbox( # <--- THIS IS THE DROPDOWN
    "Choose System Prompt Source:",
    display_options,
    index=default_index_selectbox,
    key='prompt_library_selector_actual', 
    on_change=on_prompt_selection_change,
    help="Select a pre-saved prompt, the initial default, or use/edit the content currently in the editor below."
)

# The view_edit_prompt_ui then displays st.session_state.current_system_prompt_text
view_edit_prompt_ui(
    "System Prompt for Table Generation (Active)",
    'current_system_prompt_text', 
    'system_prompt_mode',
    'system_prompt_section1',
    filename_base="active_system_prompt"
)
if st.session_state.app_step == 0:
    # ... (Generate Initial Table button and logic remains the same as your provided version) ...
    st.info("Define inputs in the sidebar, select LLMs, choose/edit the System Prompt, then click below.")
    if st.button("🚀 Generate Initial Table", type="primary"):
        mandatory_fields = ["industry", "region", "transformational_journey", "program_area"]
        validation_errors = [f"- **{field.replace('_', ' ').title()}** cannot be empty."
                             for field in mandatory_fields if not st.session_state.user_input_data.get(field, "").strip()]
        if not st.session_state.external_data_provided:
            validation_errors.append("- At least one **External Data Input** must be provided.")

        if validation_errors:
            st.error("Please fix the following input errors before proceeding:")
            for error in validation_errors: st.markdown(error)
        else:
            with st.spinner(f"Generating initial table using {st.session_state.generator_llm_name}... This may take a moment."):
                try:
                    current_year = datetime.now().year
                    future_year_delta = st.session_state.user_input_data.get("future_year", 20)
                    absolute_future_year = current_year + future_year_delta

                    format_data = st.session_state.user_input_data.copy()
                    format_data["current_year"] = current_year
                    format_data["future_year"] = absolute_future_year

                    st.session_state.formatted_user_prompt_text = USER_QUERY_TEMPLATE.format(**format_data)
                    st.session_state.learnable_system_prompt_var = tg.Variable(
                        st.session_state.current_system_prompt_text, 
                        requires_grad=True, role_description="System prompt for generating the table report"
                    )
                    st.session_state.formatted_user_prompt_var = tg.Variable(
                        st.session_state.formatted_user_prompt_text, requires_grad=False,
                        role_description="User inputs and contextual data for table generation"
                    )
                    model = tg.BlackboxLLM(llm_engine, system_prompt=st.session_state.learnable_system_prompt_var)
                    generated_table_variable = model(st.session_state.formatted_user_prompt_var)

                    st.session_state.last_generated_table_text = generated_table_variable.value
                    st.session_state.last_generated_table_variable = generated_table_variable
                    st.session_state.generated_prompt_for_eval = st.session_state.learnable_system_prompt_var.value 
                    st.session_state.app_step = 1
                    st.success("Initial table generated successfully!")
                except Exception as e:
                    handle_textgrad_exception(e, "table generation")
                    st.session_state.last_generated_table_text = ""
                    st.session_state.last_generated_table_variable = None
            st.rerun()


if st.session_state.app_step >= 1:
    st.subheader("Generated Table:")
    try_display_table(st.session_state.last_generated_table_text, "initial_gen", "initial_report")
elif st.session_state.app_step >= 1 and not st.session_state.last_generated_table_text: # Check type
    st.warning("Table generation was attempted but did not produce valid content. Please check logs or try again.")

st.markdown("---")

# --- Section 2: Evaluation (Ensure download buttons are active) ---
st.header("2. Evaluate Generated Table")
if st.session_state.app_step >= 1:
    st.info("Review the generated table above. If satisfied, or to get feedback, run the evaluation. You can also edit the Evaluation Prompt Template below.")
    view_edit_prompt_ui(
        "Evaluation Prompt Template",
        'evaluation_prompt_template_text',
        'eval_prompt_mode',
        'eval_prompt_section2',
        filename_base="evaluation_prompt_template" # Pass filename_base
    )
    # ... (Run Evaluation button and logic remains the same as your provided version) ...
    if st.button("⚖️ Run Evaluation"):
        if not st.session_state.get('last_generated_table_variable') or not st.session_state.get('generated_prompt_for_eval'):
            st.warning("Cannot evaluate. Please ensure a table was generated successfully in Step 1.")
        else:
            with st.spinner(f"Running evaluation using {st.session_state.evaluator_llm_name}... This may take a moment."):
                try:
                    eval_user_inputs = st.session_state.user_input_data
                    current_year = datetime.now().year
                    future_year_delta = eval_user_inputs.get("future_year", 20)
                    absolute_future_year = current_year + future_year_delta

                    format_data_for_eval = eval_user_inputs.copy()
                    format_data_for_eval["current_year"] = current_year
                    format_data_for_eval["future_year"] = absolute_future_year

                    eval_instruction_text = st.session_state.evaluation_prompt_template_text.format(
                        system_prompt_text=st.session_state.generated_prompt_for_eval, 
                        user_query_text=st.session_state.formatted_user_prompt_text,
                        generated_table_text=st.session_state.last_generated_table_text,
                        **format_data_for_eval
                    )
                    

                    st.session_state.loss_instruction_var = tg.Variable(
                        eval_instruction_text, requires_grad=False,
                        role_description="Instruction for evaluating the system prompt's output against the evaluation criteria and providing feedback to SYSTEM PROMPT for improvement." 
                    )
                    st.session_state.loss_fn = tg.TextLoss(st.session_state.loss_instruction_var, engine=llm_evaluator)
                    # Ensure last_generated_table_variable is valid
                    if not st.session_state.last_generated_table_variable or not hasattr(st.session_state.last_generated_table_variable, 'value'):
                        st.error("Error: `last_generated_table_variable` is not set up correctly for evaluation.")
                        raise ValueError("Generated table variable is missing or invalid.")

                    loss = st.session_state.loss_fn(st.session_state.last_generated_table_variable)

                    st.session_state.last_evaluation_output = loss.value
                    st.session_state.last_loss_object = loss # Store for potential backward pass
                    score, desc, feedback = parse_evaluation_output(loss.value)
                    st.session_state.last_evaluation_score = score
                    st.session_state.last_evaluation_description = desc
                    st.session_state.last_evaluation_feedback = feedback

                    if score is not None:
                        st.session_state.app_step = 2
                        st.success(f"Evaluation complete! Score: {score}/100")
                    else:
                        st.warning("Evaluation completed, but a valid score could not be parsed from the output. Please review the Raw Evaluation Output below.")
                except Exception as e:
                    handle_textgrad_exception(e, "evaluation")
                    st.session_state.last_evaluation_output = f"Error during evaluation: {e}" 
                    st.session_state.last_evaluation_score = None
                st.rerun()

if st.session_state.app_step >= 2:
    st.subheader("Evaluation Results:")
    if st.session_state.last_evaluation_score is not None:
        st.metric("Overall Score", f"{st.session_state.last_evaluation_score}/100")
    else:
        st.warning("No valid score was parsed from the last evaluation. Raw output is available below.")

    display_text_with_copy_and_download( 
        "Scoring Description", st.session_state.last_evaluation_description,
        height=200, key_suffix="eval_desc", filename="evaluation_scoring_description.txt",
        help_text="The evaluator's reasoning for the score."
    )
    display_text_with_copy_and_download( 
        "System Prompt Improvement Feedback", st.session_state.last_evaluation_feedback,
        height=200, key_suffix="eval_feedback", filename="evaluation_prompt_feedback.txt",
        help_text="Suggestions from the evaluator to improve the system prompt."
    )
    with st.expander("View Raw Evaluation Output"):
        display_text_with_copy_and_download( 
            "Raw Output from Evaluator LLM", st.session_state.last_evaluation_output,
            height=300, key_suffix="eval_raw_output", filename="evaluation_raw_output.txt"
        )

st.markdown("---")

# --- Section 3: System Prompt Optimization (Ensure download button for prompt) ---
st.header("3. System Prompt Optimization")
if st.session_state.app_step >= 2 and st.session_state.last_evaluation_score is not None:
    st.info("The system prompt below (from selected source or last optimized state) will be improved. Adjust parameters as needed.")
    view_edit_prompt_ui(
        "Current System Prompt for Optimization",
        'current_system_prompt_text',
        'system_prompt_mode', 
        'system_prompt_section3',
        filename_base="system_prompt_for_optimization" # Pass filename_base
    )
    # ... (Optimization parameters and Run Optimization button/logic remains the same as your provided version) ...
    col_opt_params1, col_opt_params2 = st.columns(2)
    with col_opt_params1:
        st.session_state.num_opt_steps = st.number_input(
            "Number of Optimization Steps", min_value=1, max_value=20, 
            value=st.session_state.num_opt_steps, format="%d", key='num_opt_steps_input',
            help="How many times the optimizer will attempt to refine the system prompt."
        )
    with col_opt_params2:
        st.session_state.target_score_thresh = st.number_input(
            "Target Score Threshold", min_value=0, max_value=100,
            value=st.session_state.target_score_thresh, format="%d", key='target_score_thresh_input',
            help="Optimization will stop if a score >= this value is achieved."
        )

    if st.button("✨ Run Optimization", type="primary"):
        if not st.session_state.get('formatted_user_prompt_var') or st.session_state.last_evaluation_score is None:
            st.warning("Cannot optimize. Ensure a table has been generated and successfully evaluated in prior steps.")
        else:
            with st.spinner(f"Running optimization for {st.session_state.num_opt_steps} steps... This will take time."):
                st.session_state.learnable_system_prompt_var = tg.Variable(
                    st.session_state.current_system_prompt_text, # Uses the potentially loaded/edited prompt
                    requires_grad=True, role_description="System prompt being optimized by TextGrad"
                )
                model = tg.BlackboxLLM(llm_engine, system_prompt=st.session_state.learnable_system_prompt_var)
                optimizer = tg.TGD(parameters=[st.session_state.learnable_system_prompt_var])

                # Initialize tracking for best result, starting with the last manually evaluated one
                best_score = st.session_state.last_evaluation_score
                best_prompt = st.session_state.generated_prompt_for_eval # Prompt that achieved the last manual score
                best_table = st.session_state.last_generated_table_text
                best_description = st.session_state.last_evaluation_description
                best_feedback = st.session_state.last_evaluation_feedback
                best_step_num = 0 # 0 for initial state before optimization loop

                st.session_state.optimization_history = [] # Clear history for a new run
                optimization_progress = st.progress(0)
                status_text = st.empty()
                opt_user_inputs = st.session_state.user_input_data # Consistent inputs for optimization

                for step in range(st.session_state.num_opt_steps):
                    current_opt_step_display = step + 1
                    status_text.text(f"Optimization Step {current_opt_step_display}/{st.session_state.num_opt_steps}...")
                    optimization_progress.progress(current_opt_step_display / st.session_state.num_opt_steps)

                    try:
                        prompt_before_update_this_step = st.session_state.learnable_system_prompt_var.value
                        generated_table_var_opt = model(st.session_state.formatted_user_prompt_var)
                        current_table_text_opt = generated_table_var_opt.value

                        current_year = datetime.now().year
                        future_year_delta = opt_user_inputs.get("future_year", 20)
                        abs_future_year = current_year + future_year_delta
                        format_data_eval_opt = opt_user_inputs.copy()
                        format_data_eval_opt["current_year"] = current_year
                        format_data_eval_opt["future_year"] = abs_future_year

                        eval_instr_opt = st.session_state.evaluation_prompt_template_text.format(
                            system_prompt_text=prompt_before_update_this_step, 
                            user_query_text=st.session_state.formatted_user_prompt_text,
                            generated_table_text=current_table_text_opt,
                            **format_data_eval_opt
                        )
                        loss_instr_var_opt = tg.Variable(eval_instr_opt, requires_grad=False, role_description="Evaluation instruction for optimization step")
                        loss_fn_opt = tg.TextLoss(loss_instr_var_opt, engine=llm_evaluator)
                        loss_opt = loss_fn_opt(generated_table_var_opt)
                        current_eval_output_opt = loss_opt.value

                        score_opt, desc_opt, feedback_opt = parse_evaluation_output(current_eval_output_opt)

                        history_entry = {
                            "step": current_opt_step_display, "prompt": prompt_before_update_this_step,
                            "table": current_table_text_opt, "score": score_opt,
                            "description": desc_opt, "feedback": feedback_opt,
                            "evaluation_raw": current_eval_output_opt
                        }
                        st.session_state.optimization_history.append(history_entry)

                        if score_opt is not None and score_opt > best_score:
                            best_score, best_prompt, best_table = score_opt, prompt_before_update_this_step, current_table_text_opt
                            best_description, best_feedback, best_step_num = desc_opt, feedback_opt, current_opt_step_display
                            status_text.text(f"Step {current_opt_step_display}: New best score {best_score}!")

                        if score_opt is not None and score_opt >= st.session_state.target_score_thresh:
                            status_text.text(f"Target score reached at step {current_opt_step_display}! Score: {score_opt}.")
                            st.session_state.current_system_prompt_text = prompt_before_update_this_step 
                            break 

                        if score_opt is not None: 
                            loss_opt.backward()
                            optimizer.step()
                            optimizer.zero_grad()
                        else:
                            st.warning(f"Step {current_opt_step_display}: Invalid score parsed. Skipping optimizer update for this step.")
                            
                    except Exception as e_opt:
                        st.error(f"Error in optimization step {current_opt_step_display}: {e_opt}")
                        # Log the error in history
                        error_history_entry = {
                            "step": current_opt_step_display, 
                            "prompt": st.session_state.learnable_system_prompt_var.value if 'learnable_system_prompt_var' in st.session_state and st.session_state.learnable_system_prompt_var else "N/A",
                            "table": "Error during this step.", "score": None,
                            "description": f"Error: {e_opt}", "feedback": "Optimization step failed.",
                            "evaluation_raw": f"Error: {e_opt}"
                        }
                        st.session_state.optimization_history.append(error_history_entry)
                        
                status_text.text("Optimization process finished.")
                optimization_progress.progress(1.0)

                st.session_state.best_optimized_system_prompt_text = best_prompt
                st.session_state.best_optimized_table_text = best_table
                st.session_state.best_optimized_score = best_score
                st.session_state.best_optimized_description = best_description
                st.session_state.best_optimized_feedback = best_feedback
                st.session_state.best_optimized_step = best_step_num

                # Update the main editable system prompt to the *final* state of the learnable variable
                if st.session_state.get('learnable_system_prompt_var') is not None:
                   st.session_state.current_system_prompt_text = st.session_state.learnable_system_prompt_var.value

                st.session_state.app_step = 3
                # Increment key to force prompt library selectbox to re-fetch options if a new prompt was saved during optimization (though save is manual after)
                st.session_state.prompt_library_selector_key += 1
                st.rerun()

elif st.session_state.app_step >= 2:
    st.info("Optimization requires a successful evaluation with a parsed score (from Step 2).")


st.markdown("---")

# --- Section 4: Best Optimization Result (Ensure download and SAVE buttons are active) ---
st.header("4. Best Optimization Result")
if st.session_state.app_step >= 3 and st.session_state.best_optimized_score is not None:
    st.success(f"Optimization run complete. The best result achieved is shown below.")
    st.metric(
        "Highest Score Achieved During Optimization",
        f"{st.session_state.best_optimized_score}/100",
        help=(f"Achieved at optimization step {st.session_state.best_optimized_step}."
              if st.session_state.best_optimized_step > 0
              else "This was the score from the initial evaluation before optimization steps.")
    )

    with st.expander("View Best Optimized System Prompt", expanded=True): # Expanded by default
        display_text_with_copy_and_download( 
            "Best System Prompt Content",
            st.session_state.best_optimized_system_prompt_text,
            height=300, key_suffix="best_opt_prompt",
            filename="best_optimized_system_prompt.txt",
            help_text="This prompt achieved the highest score during the optimization process."
        )
        # --- Save Prompt Button ---
        prompt_name_suggestion = f"Optimized_Score{st.session_state.best_optimized_score}_Step{st.session_state.best_optimized_step}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        col_save_name, col_save_btn = st.columns([3,1.2])
        with col_save_name:
            save_prompt_name = st.text_input(
                "Filename to save this prompt (no extension):",
                value=prompt_name_suggestion.replace(" ", "_").replace(":", ""), # Sanitize a bit
                key="save_best_prompt_name_input",
                help="Enter a descriptive name. It will be saved as '.txt' in 'saved_prompts/' folder."
            )
        with col_save_btn:
            st.markdown("<br>", unsafe_allow_html=True) # Align button a bit
            if st.button("💾 Save this Best Prompt to Library", key="save_best_prompt_button_actual"):
                if save_prompt_name and save_prompt_name.strip():
                    # Extract some key user inputs for context
                    relevant_inputs_for_context = {
                        k: st.session_state.user_input_data.get(k) 
                        for k in ["industry", "region", "transformational_journey", "program_area"] 
                        if st.session_state.user_input_data.get(k)
                    }
                    if save_prompt_to_library(
                        save_prompt_name.strip(), # Use the user-provided name
                        st.session_state.best_optimized_system_prompt_text,
                        score=st.session_state.best_optimized_score,
                        related_inputs=relevant_inputs_for_context
                    ):
                        # Force refresh of the prompt library selector
                        st.session_state.prompt_library_selector_key += 1
                        st.rerun() # Rerun to update the selectbox options
                else:
                    st.warning("Please enter a valid name for the prompt before saving.")


    st.subheader("Generated Table (from Best Prompt):")
    try_display_table(st.session_state.best_optimized_table_text, "best_opt", "best_optimized_report")
    
    with st.expander("View Evaluation Details for Best Result", expanded=False):
        st.markdown("##### System Prompt for this Best Result:") # Already shown above, but can repeat if desired
        # display_text_with_copy_and_download(...) 
        st.markdown("##### Evaluation Feedback for this Best Result:")
        display_text_with_copy_and_download(
            "Feedback (Best Result)", 
            st.session_state.best_optimized_feedback, 
            height=150, 
            key_suffix="feedback_best_feedback_view",
            filename="best_result_associated_feedback.txt"
        )
        st.markdown("##### Scoring Description for this Best Result:")
        display_text_with_copy_and_download(
            "Scoring Description (Best Result)",
            st.session_state.best_optimized_description,
            height=150, key_suffix="feedback_best_desc_view",
            filename="best_result_associated_description.txt"
        )

elif st.session_state.app_step >= 3:
    st.info("Optimization was run, but no valid best score was recorded or an error occurred. Check the history for details.")

st.markdown("---")

# --- Section 5: Optimization History (Ensure download buttons are active) ---
st.header("5. Optimization History")
if 'optimization_history' in st.session_state and st.session_state.optimization_history:
    with st.expander("View Step-by-Step Optimization Details", expanded=False):
        # Display history in reverse chronological order (most recent step first)
        history_list = st.session_state.optimization_history
        for i, entry in enumerate(reversed(history_list)): # Iterate reversed list
            actual_step_number = entry['step'] # Use the step number from the entry
            is_best_this_entry = (actual_step_number == st.session_state.best_optimized_step and
                                  entry['score'] == st.session_state.best_optimized_score and
                                  entry['score'] is not None)
            
            header_md = f"##### Step {actual_step_number}"
            if is_best_this_entry:
                header_md += " (🌟 Corresponds to Best Score Achieved)"
            
            with st.container(): # Use container for better visual separation
                st.markdown(header_md)
                score_display = f"{entry['score']}/100" if entry['score'] is not None else "N/A (Error or Parse Issue)"
                if is_best_this_entry:
                    st.markdown(f"**Score:** <span style='color:green; font-weight:bold;'>🌟 {score_display}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**Score:** {score_display}")

                col_hist_prompt, col_hist_details = st.columns([0.6, 0.4]) 
                with col_hist_prompt:
                    display_text_with_copy_and_download( 
                        f"System Prompt Used (Step {actual_step_number})", entry.get('prompt',""), height=250,
                        key_suffix=f"hist_prompt_{actual_step_number}_{i}", # Ensure unique key
                        filename=f"history_step_{actual_step_number}_prompt.txt"
                    )
                with col_hist_details:
                    display_text_with_copy_and_download( 
                        f"Evaluator Feedback (Step {actual_step_number})", entry.get('feedback',""), height=100,
                        key_suffix=f"hist_feed_{actual_step_number}_{i}",  # Ensure unique key
                        filename=f"history_step_{actual_step_number}_feedback.txt"
                    )
                    display_text_with_copy_and_download( 
                        f"Scoring Description (Step {actual_step_number})", entry.get('description',""), height=100,
                        key_suffix=f"hist_desc_{actual_step_number}_{i}", # Ensure unique key
                        filename=f"history_step_{actual_step_number}_description.txt"
                    )
                
                show_full_table_key = f"show_full_table_step_{actual_step_number}_{i}" # Ensure unique key
                if st.checkbox("Show Full Generated Table for this step", key=show_full_table_key, value=False):
                    table_content_history = entry.get('table')
                    if table_content_history and isinstance(table_content_history, str):
                         try_display_table(table_content_history, f"hist_table_{actual_step_number}_{i}", f"history_step_{actual_step_number}_report")
                    else:
                        st.info(f"No table content or invalid table format for step {actual_step_number}.")
                st.markdown("---") 
else:
    st.info("No optimization history recorded for this session yet. Run optimization (Section 3) to populate this.")

st.markdown("---")

# --- Section 6: Understanding Optimization (Remains the same) ---
render_understanding_optimization_section()