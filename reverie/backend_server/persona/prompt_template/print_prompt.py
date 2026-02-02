"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: print_prompt.py
Description: For printing prompts when the setting for verbose is set to True.
"""

# Minimal imports — this module only prints prompt-related debug information.
# Avoid wildcard imports and unnecessary sys.path manipulation to keep static
# analysis and linting clean.


def _noop():
    """Placeholder to indicate this module intentionally keeps a tiny surface."""
    return None

##############################################################################
#                    PERSONA Chapter 1: Prompt Structures                    #
##############################################################################


def print_run_prompts(
    prompt_template=None,
    persona=None,
    gpt_param=None,
    prompt_input=None,
    prompt=None,
    output=None,
):
    print(f"=== {prompt_template}")
    print("~~~ persona    ---------------------------------------------------")
    print(persona.name, "\n")
    print("~~~ gpt_param ----------------------------------------------------")
    print(gpt_param, "\n")
    print("~~~ prompt_input    ----------------------------------------------")
    print(prompt_input, "\n")
    print("~~~ prompt    ----------------------------------------------------")
    print(prompt, "\n")
    print("~~~ output    ----------------------------------------------------")
    print(output, "\n")
    print("=== END ==========================================================")
    print("\n\n\n")
