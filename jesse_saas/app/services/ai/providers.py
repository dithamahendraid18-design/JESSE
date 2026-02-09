import requests
import os

def call_openai_compatible(api_key, base_url, model, system, user, temp, tokens, history):
    if base_url.endswith('/chat/completions'): base_url = base_url.replace('/chat/completions', '')
    target_url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user})
    
    payload = {"model": model, "messages": messages, "temperature": temp, "max_tokens": tokens}
    resp = requests.post(target_url, headers=headers, json=payload, timeout=25)
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']

def call_groq(api_key, model, system, user, temp, tokens, history):
    return call_openai_compatible(api_key, "https://api.groq.com/openai/v1", model, system, user, temp, tokens, history)

def call_openai(api_key, model, system, user, temp, tokens, history):
    return call_openai_compatible(api_key, "https://api.openai.com/v1", model, system, user, temp, tokens, history)

def call_anthropic(api_key, model, system, user, temp, tokens, history):
    url = "https://api.anthropic.com/v1/messages"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    
    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user})

    payload = {"model": model, "system": system, "messages": messages, "max_tokens": tokens, "temperature": temp}
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()['content'][0]['text']
