"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.
"""

import json
import random
import os
import time
import logging
import openai
import requests

# Backends: 'openai' (default), 'ollama', 'copilot'
LLM_BACKEND = os.environ.get("LLM_BACKEND", "openai").lower()
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama2")
COPILOT_API_URL = os.environ.get("COPILOT_API_URL")
COPILOT_API_KEY = os.environ.get("COPILOT_API_KEY")
# Default model to use for GitHub Copilot backend when none is specified
COPILOT_DEFAULT_MODEL = os.environ.get("COPILOT_DEFAULT_MODEL", "grok-code-fast-1")

# Legacy: attempt to import openai_api_key from utils (keeps backward compatibility).
# Preferred: set OPENAI_API_KEY in your environment (see README and .env.example).
try:
    from utils import openai_api_key  # type: ignore
except Exception:
    openai_api_key = (
        os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API") or None
    )

if openai_api_key:
    openai.api_key = openai_api_key
else:
    logging.warning(
        "OPENAI_API_KEY not found in env nor utils.py; OpenAI calls may fail"
    )


# Helper: call OpenAI with exponential backoff for transient errors
def _openai_with_backoff(callable_func, repeat=3, backoff_factor=1, *args, **kwargs):
    last_exc = None
    for i in range(repeat):
        try:
            return callable_func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            logging.warning(f"OpenAI call failed (attempt {i+1}/{repeat}): {e}")
            if i < repeat - 1:
                time.sleep(backoff_factor * (2**i))
    # re-raise the last exception for callers to handle
    raise last_exc


def temp_sleep(seconds=0.1):
    time.sleep(seconds)


def ChatGPT_single_request(prompt):
    temp_sleep()

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]


# ============================================================================
# #####################[SECTION 1: CHATGPT-3 STRUCTURE] ######################
# ============================================================================


def GPT4_request(prompt, timeout=20, repeat=3):
    """Given a prompt, make a GPT-4 request with retries and timeout."""
    temp_sleep()
    try:
        completion = _openai_with_backoff(
            lambda **kw: openai.ChatCompletion.create(**kw),
            repeat=repeat,
            backoff_factor=1,
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            request_timeout=timeout,
        )
        return completion["choices"][0]["message"]["content"]
    except Exception:
        logging.exception("GPT4 request failed")
        return "ChatGPT ERROR"


def _ollama_parse_response(resp):
    """Try to parse common Ollama response shapes and return text content."""
    try:
        body = resp.json()
    except Exception:
        # not JSON; return raw text
        return resp.text

    # Try common shapes
    if isinstance(body, dict):
        if "results" in body and isinstance(body["results"], list):
            first = body["results"][0]
            # content nested in different keys depending on Ollama version
            return (
                first.get("content")
                or first.get("output")
                or first.get("text")
                or json.dumps(first)
            )
        if "output" in body:
            return body["output"]
        if "text" in body:
            return body["text"]
        # Fallback to JSON string
        return json.dumps(body)
    return str(body)


def Ollama_request(prompt, model=None, timeout=20, repeat=3):
    """Call an Ollama HTTP endpoint and return the generated text.

    This implementation is intentionally permissive about the exact JSON
    shape returned by different Ollama versions; tests mock `requests.post`.
    """
    url = os.environ.get("OLLAMA_API_URL", OLLAMA_API_URL)

    def _call():
        payload = {"model": model or os.environ.get("OLLAMA_MODEL", OLLAMA_MODEL), "prompt": prompt}
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r

    try:
        resp = _openai_with_backoff(lambda **kw: _call(), repeat=repeat, backoff_factor=1)
        return _ollama_parse_response(resp)
    except Exception:
        logging.exception("Ollama request failed")
        return "ChatGPT ERROR"


from persona.prompt_template.copilot_token import resolve_copilot_api_token


def Copilot_request(prompt, model=None, timeout=20, repeat=3):
    """Call a configured Copilot HTTP endpoint.

    Two modes:
    - If `COPILOT_API_URL` env var is set, use it directly (proxy mode).
    - Otherwise, attempt to exchange a GitHub token (COPILOT_GITHUB_TOKEN / GH_TOKEN / GITHUB_TOKEN)
      for a Copilot token and derived base URL using `resolve_copilot_api_token`.

    The function injects `Authorization: Bearer <copilot_token>` into requests.
    """
    # 1) explicit override
    explicit_url = os.environ.get("COPILOT_API_URL")
    headers = {}

    if explicit_url:
        url = explicit_url
    else:
        # Try to resolve via GitHub token exchange
        try:
            info = resolve_copilot_api_token()
            url = info["baseUrl"]
            token = info["token"]
            headers["Authorization"] = f"Bearer {token}"
        except Exception:
            raise RuntimeError("COPILOT_API_URL not configured and Copilot token exchange failed")

    def _call():
        # If model is not provided, default to the configured Copilot default model
        _model = model or os.environ.get("COPILOT_DEFAULT_MODEL", COPILOT_DEFAULT_MODEL)
        payload = {"prompt": prompt, "model": _model}
        r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r

    try:
        resp = _openai_with_backoff(lambda **kw: _call(), repeat=repeat, backoff_factor=1)
        try:
            body = resp.json()
            return body.get("result") or body.get("output") or body.get("text") or json.dumps(body)
        except Exception:
            return resp.text
    except Exception:
        logging.exception("Copilot request failed")
        return "ChatGPT ERROR"


def ChatGPT_request(prompt, timeout=15, repeat=3):
    """Make a ChatGPT (gpt-3.5-turbo) request with retries and timeout.

    If environment `LLM_BACKEND` is set to `ollama` or `copilot`, dispatch to
    the respective adapter so the rest of the codebase can remain unchanged.
    """
    backend = os.environ.get("LLM_BACKEND", "openai").lower()
    if backend == "ollama":
        return Ollama_request(prompt, timeout=timeout, repeat=repeat)
    if backend == "copilot":
        return Copilot_request(prompt, timeout=timeout, repeat=repeat)

    try:
        completion = _openai_with_backoff(
            lambda **kw: openai.ChatCompletion.create(**kw),
            repeat=repeat,
            backoff_factor=1,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            request_timeout=timeout,
        )
        return completion["choices"][0]["message"]["content"]
    except Exception:
        logging.exception("ChatGPT request failed")
        return "ChatGPT ERROR"


def GPT4_safe_generate_response(
    prompt,
    example_output,
    special_instruction,
    repeat=3,
    fail_safe_response="error",
    func_validate=None,
    func_clean_up=None,
    verbose=False,
):
    prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
    prompt += (
        f"Output the response to the prompt above in json. {special_instruction}\n"
    )
    prompt += "Example output json:\n"
    prompt += '{"output": "' + str(example_output) + '"}'

    if verbose:
        print("CHAT GPT PROMPT")
        print(prompt)

    for i in range(repeat):

        try:
            curr_gpt_response = GPT4_request(prompt).strip()
            end_index = curr_gpt_response.rfind("}") + 1
            curr_gpt_response = curr_gpt_response[:end_index]
            curr_gpt_response = json.loads(curr_gpt_response)["output"]

            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)

            if verbose:
                print("---- repeat count: \n", i, curr_gpt_response)
                print(curr_gpt_response)
                print("~~~~")

        except Exception:
            logging.exception("GPT4_safe_generate_response parse/validation error")
            pass

    return False


def ChatGPT_safe_generate_response(
    prompt,
    example_output,
    special_instruction,
    repeat=3,
    fail_safe_response="error",
    func_validate=None,
    func_clean_up=None,
    verbose=False,
):
    # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
    prompt = '"""\n' + prompt + '\n"""\n'
    prompt += (
        f"Output the response to the prompt above in json. {special_instruction}\n"
    )
    prompt += "Example output json:\n"
    prompt += '{"output": "' + str(example_output) + '"}'

    if verbose:
        print("CHAT GPT PROMPT")
        print(prompt)

    for i in range(repeat):

        try:
            curr_gpt_response = ChatGPT_request(prompt).strip()
            end_index = curr_gpt_response.rfind("}") + 1
            curr_gpt_response = curr_gpt_response[:end_index]
            curr_gpt_response = json.loads(curr_gpt_response)["output"]

            # print ("---ashdfaf")
            # print (curr_gpt_response)
            # print ("000asdfhia")

            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)

            if verbose:
                print("---- repeat count: \n", i, curr_gpt_response)
                print(curr_gpt_response)
                print("~~~~")

        except Exception:
            logging.exception("ChatGPT_safe_generate_response parse/validation error")
            pass

    return False


def ChatGPT_safe_generate_response_OLD(
    prompt,
    repeat=3,
    fail_safe_response="error",
    func_validate=None,
    func_clean_up=None,
    verbose=False,
):
    if verbose:
        print("CHAT GPT PROMPT")
        print(prompt)

    for i in range(repeat):
        try:
            curr_gpt_response = ChatGPT_request(prompt).strip()
            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)
            if verbose:
                print(f"---- repeat count: {i}")
                print(curr_gpt_response)
                print("~~~~")

        except Exception:
            logging.exception("ChatGPT_safe_generate_response_OLD parse/validation error")
            pass
    print("FAIL SAFE TRIGGERED")
    return fail_safe_response


# ============================================================================
# ###################[SECTION 2: ORIGINAL GPT-3 STRUCTURE] ###################
# ============================================================================


def GPT_request(prompt, gpt_parameter):
    """
    Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
    server and returns the response.
    ARGS:
      prompt: a str prompt
      gpt_parameter: a python dictionary with the keys indicating the names of
                     the parameter and the values indicating the parameter
                     values.
    RETURNS:
      a str of GPT-3's response.
    """
    temp_sleep()
    try:
        response = openai.Completion.create(
            model=gpt_parameter["engine"],
            prompt=prompt,
            temperature=gpt_parameter["temperature"],
            max_tokens=gpt_parameter["max_tokens"],
            top_p=gpt_parameter["top_p"],
            frequency_penalty=gpt_parameter["frequency_penalty"],
            presence_penalty=gpt_parameter["presence_penalty"],
            stream=gpt_parameter["stream"],
            stop=gpt_parameter["stop"],
        )
        return response.choices[0].text
    except Exception:
        logging.exception("TOKEN LIMIT EXCEEDED")
        return "TOKEN LIMIT EXCEEDED"


def generate_prompt(curr_input, prompt_lib_file):
    """
    Takes in the current input (e.g. comment that you want to classifiy) and
    the path to a prompt file. The prompt file contains the raw str prompt that
    will be used, which contains the following substr: !<INPUT>! -- this
    function replaces this substr with the actual curr_input to produce the
    final promopt that will be sent to the GPT3 server.
    ARGS:
      curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                  INPUT, THIS CAN BE A LIST.)
      prompt_lib_file: the path to the promopt file.
    RETURNS:
      a str prompt that will be sent to OpenAI's GPT server.
    """
    if type(curr_input) == type("string"):
        curr_input = [curr_input]
    curr_input = [str(i) for i in curr_input]

    f = open(prompt_lib_file, "r")
    prompt = f.read()
    f.close()
    for count, i in enumerate(curr_input):
        prompt = prompt.replace(f"!<INPUT {count}>!", i)
    if "<commentblockmarker>###</commentblockmarker>" in prompt:
        prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
    return prompt.strip()


def safe_generate_response(
    prompt,
    gpt_parameter,
    repeat=5,
    fail_safe_response="error",
    func_validate=None,
    func_clean_up=None,
    verbose=False,
):
    if verbose:
        print(prompt)

    for i in range(repeat):
        curr_gpt_response = GPT_request(prompt, gpt_parameter)
        if func_validate(curr_gpt_response, prompt=prompt):
            return func_clean_up(curr_gpt_response, prompt=prompt)
        if verbose:
            print("---- repeat count: ", i, curr_gpt_response)
            print(curr_gpt_response)
            print("~~~~")
    return fail_safe_response


def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"
    return openai.Embedding.create(input=[text], model=model)["data"][0]["embedding"]


if __name__ == "__main__":
    gpt_parameter = {
        "engine": "text-davinci-003",
        "max_tokens": 50,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": ['"'],
    }
    curr_input = ["driving to a friend's house"]
    prompt_lib_file = "prompt_template/test_prompt_July5.txt"
    prompt = generate_prompt(curr_input, prompt_lib_file)

    def __func_validate(gpt_response):
        if len(gpt_response.strip()) <= 1:
            return False
        if len(gpt_response.strip().split(" ")) > 1:
            return False
        return True

    def __func_clean_up(gpt_response):
        cleaned_response = gpt_response.strip()
        return cleaned_response

    output = safe_generate_response(
        prompt, gpt_parameter, 5, "rest", __func_validate, __func_clean_up, True
    )

    print(output)
