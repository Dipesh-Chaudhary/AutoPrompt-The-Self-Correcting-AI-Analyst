import re
import os
import json
from datetime import datetime

SAVED_PROMPTS_DIR = "saved_prompts"


def ensure_saved_prompts_dir():
    """Ensures the directory for saving prompts exists."""
    if not os.path.exists(SAVED_PROMPTS_DIR):
        os.makedirs(SAVED_PROMPTS_DIR)

def save_prompt_to_library(prompt_name, prompt_content, score=None, related_inputs=None):
    """Saves a system prompt to the library."""
    ensure_saved_prompts_dir()
    filename_base = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in prompt_name).rstrip()
    filename = f"{filename_base}.txt"
    filepath = os.path.join(SAVED_PROMPTS_DIR, filename)
    
    file_content = f"# Prompt Name: {prompt_name}\n"
    if score is not None:
        file_content += f"# Associated Score: {score}\n"
    if related_inputs:
        # Quick dump of a few key inputs for context, can be expanded
        context_inputs = {k: related_inputs.get(k) for k in ['industry', 'region', 'transformational_journey'] if related_inputs.get(k)}
        if context_inputs:
            file_content += f"# Context Inputs: {json.dumps(context_inputs)}\n"
    file_content += f"# Saved At: {datetime.now().isoformat()}\n"
    file_content += "# --- BEGIN PROMPT ---\n"
    file_content += prompt_content
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file_content)
        return True
    except Exception as e:
        print(f"Failed to save prompt '{prompt_name}': {e}") # Add a print for debugging
        return False

def load_prompt_from_library(filename):
    """Loads a system prompt from the library."""
    ensure_saved_prompts_dir()
    filepath = os.path.join(SAVED_PROMPTS_DIR, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        prompt_content_lines = []
        found_marker = False
        for line in lines:
            if line.strip() == "# --- BEGIN PROMPT ---":
                found_marker = True
                continue
            if found_marker:
                prompt_content_lines.append(line)
        
        if not found_marker and lines:
            return "".join(lines) # Fallback: load whole file if no marker but content exists
        elif not prompt_content_lines and not found_marker and not lines: # File is truly empty
            return ""
        elif not prompt_content_lines and found_marker: # Marker exists, but no content after
             return ""

        return "".join(prompt_content_lines)
    except FileNotFoundError:
        print(f"Prompt file '{filename}' not found in '{SAVED_PROMPTS_DIR}'.") # Add a print for debugging
        return None
    except Exception as e:
        print(f"Failed to load prompt '{filename}': {e}") # Add a print for debugging
        return None


def get_saved_prompts_list():
    """Returns a list of filenames of saved prompts, sorted by modification time (newest first)."""
    ensure_saved_prompts_dir()
    try:
        files = [f for f in os.listdir(SAVED_PROMPTS_DIR) if f.endswith(".txt")]
        # Sort files by modification time, newest first
        files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVED_PROMPTS_DIR, f)), reverse=True)
        return files
    except Exception as e:
        print(f"Error listing saved prompts: {e}") # Add a print for debugging
        return []


def parse_evaluation_output(output_text):
    """
    Parses scoring description, score, and feedback from the evaluator LLM's output.
    Assumes the structure specified in EVALUATION_PROMPT_TEMPLATE.
    """
    score = None
    scoring_description = "Could not parse scoring description from evaluation output."
    feedback = "Could not parse feedback from evaluation output."

    if not output_text or not isinstance(output_text, str):
        return score, scoring_description, feedback

    try:
        # Regex for Scoring Description
        # This now captures EVERYTHING after "## Scoring Description:"
        # up to the next main header or end of string.
        desc_match = re.search(
            r"## Scoring Description:\s*(.*?)(?=\n## Overall Score:|\n## System Prompt Improvement Feedback:|\Z)",
            output_text, re.IGNORECASE | re.DOTALL
        )
        if desc_match:
            scoring_description = desc_match.group(1).strip()
        
        # Regex for Overall Score
        score_match = re.search(
            r"## Overall Score:\s*`?score`?:\s*(\d+)",
            output_text, re.IGNORECASE
        )
        if score_match:
            try:
                score = int(score_match.group(1))
            except ValueError:
                print(f"Warning: Could not convert score to int: {score_match.group(1)}")

        # Regex for System Prompt Improvement Feedback
        # This now captures EVERYTHING after "## System Prompt Improvement Feedback:"
        # up to the end of the string.
        feedback_match = re.search(
            r"## System Prompt Improvement Feedback:\s*(.*)",
            output_text, re.IGNORECASE | re.DOTALL
        )
        if feedback_match:
            feedback = feedback_match.group(1).strip()
            
    except Exception as e:
        print(f"Error parsing evaluation output: {e}")

    return score, scoring_description, feedback






# import re
# import os
# import json
# from datetime import datetime

# SAVED_PROMPTS_DIR = "saved_prompts"


# def ensure_saved_prompts_dir():
#     """Ensures the directory for saving prompts exists."""
#     if not os.path.exists(SAVED_PROMPTS_DIR):
#         os.makedirs(SAVED_PROMPTS_DIR)

# def save_prompt_to_library(prompt_name, prompt_content, score=None, related_inputs=None):
#     """Saves a system prompt to the library."""
#     ensure_saved_prompts_dir()
#     filename_base = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in prompt_name).rstrip()
#     filename = f"{filename_base}.txt"
#     filepath = os.path.join(SAVED_PROMPTS_DIR, filename)
    
#     file_content = f"# Prompt Name: {prompt_name}\n"
#     if score is not None:
#         file_content += f"# Associated Score: {score}\n"
#     if related_inputs:
#         # Quick dump of a few key inputs for context, can be expanded
#         context_inputs = {k: related_inputs.get(k) for k in ['industry', 'region', 'transformational_journey'] if related_inputs.get(k)}
#         if context_inputs:
#             file_content += f"# Context Inputs: {json.dumps(context_inputs)}\n"
#     file_content += f"# Saved At: {datetime.now().isoformat()}\n"
#     file_content += "# --- BEGIN PROMPT ---\n"
#     file_content += prompt_content
    
#     try:
#         with open(filepath, "w", encoding="utf-8") as f:
#             f.write(file_content)
#         return True
#     except Exception as e:
#         print(f"Failed to save prompt '{prompt_name}': {e}") # Add a print for debugging
#         return False

# def load_prompt_from_library(filename):
#     """Loads a system prompt from the library."""
#     ensure_saved_prompts_dir()
#     filepath = os.path.join(SAVED_PROMPTS_DIR, filename)
#     try:
#         with open(filepath, "r", encoding="utf-8") as f:
#             lines = f.readlines()
#         prompt_content_lines = []
#         found_marker = False
#         for line in lines:
#             if line.strip() == "# --- BEGIN PROMPT ---":
#                 found_marker = True
#                 continue
#             if found_marker:
#                 prompt_content_lines.append(line)
        
#         if not found_marker and lines:
#             return "".join(lines) # Fallback: load whole file if no marker but content exists
#         elif not prompt_content_lines and not found_marker and not lines: # File is truly empty
#             return ""
#         elif not prompt_content_lines and found_marker: # Marker exists, but no content after
#              return ""

#         return "".join(prompt_content_lines)
#     except FileNotFoundError:
#         print(f"Prompt file '{filename}' not found in '{SAVED_PROMPTS_DIR}'.") # Add a print for debugging
#         return None
#     except Exception as e:
#         print(f"Failed to load prompt '{filename}': {e}") # Add a print for debugging
#         return None


# def get_saved_prompts_list():
#     """Returns a list of filenames of saved prompts, sorted by modification time (newest first)."""
#     ensure_saved_prompts_dir()
#     try:
#         files = [f for f in os.listdir(SAVED_PROMPTS_DIR) if f.endswith(".txt")]
#         # Sort files by modification time, newest first
#         files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVED_PROMPTS_DIR, f)), reverse=True)
#         return files
#     except Exception as e:
#         print(f"Error listing saved prompts: {e}") # Add a print for debugging
#         return []


# def parse_evaluation_output(output_text):
#     """
#     Parses scoring description, score, and feedback from the evaluator LLM's output.
#     Assumes the structure specified in EVALUATION_PROMPT_TEMPLATE.
#     """
#     score = None
#     scoring_description = "Could not parse scoring description from evaluation output."
#     feedback = "Could not parse feedback from evaluation output."

#     if not output_text or not isinstance(output_text, str):
#         return score, scoring_description, feedback

#     try:
#         # Regex for Scoring Description
#         # Made pattern more flexible with .*? at the start of the first line
#         # to account for any pre-text before the ## header.
#         desc_match = re.search(
#             r".*?## Scoring Description:\s*`?scoring description`?:\s*(.*?)(?=\n## Overall Score:|\n## System Prompt Improvement Feedback:|\Z)",
#             output_text, re.IGNORECASE | re.DOTALL
#         )
#         if desc_match:
#             scoring_description = desc_match.group(1).strip()
        
#         # Regex for Overall Score
#         score_match = re.search(
#             r"## Overall Score:\s*`?score`?:\s*(\d+)",
#             output_text, re.IGNORECASE
#         )
#         if score_match:
#             try:
#                 score = int(score_match.group(1))
#             except ValueError:
#                 print(f"Warning: Could not convert score to int: {score_match.group(1)}")

#         # Regex for System Prompt Improvement Feedback
#         feedback_match = re.search(
#             r"## System Prompt Improvement Feedback:\s*`?feedback`?:\s*(.*)",
#             output_text, re.IGNORECASE | re.DOTALL
#         )
#         if feedback_match:
#             feedback = feedback_match.group(1).strip()
            
#     except Exception as e:
#         print(f"Error parsing evaluation output: {e}")

#     return score, scoring_description, feedback






