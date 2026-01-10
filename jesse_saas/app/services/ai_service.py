import os
from groq import Groq

# Initialize Groq Client
# Ensure GROQ_API_KEY is in your .env
client = None

def get_client():
    global client
    if client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            client = Groq(api_key=api_key)
    return client

def generate_smart_reply(user_message, client_model, kb):
    """
    Generates a response using Groq (Llama 3.1) based on the restaurant's Knowledge Base.
    """
    groq = get_client()
    if not groq:
        return "System Error: AI Service not configured (Missing API Key)."

    # Construct System Prompt
    system_prompt = f"""
You are the AI Concierge for {client_model.restaurant_name}.
Your job is to answer guest questions strictly based on the provided context.
Be polite, concise, and helpful. Keep responses under 50 words.

CONTEXT:
- About Us: {kb.about_us or 'Not specified'}
- Opening Hours: {kb.opening_hours or 'Not specified'}
- Address: {kb.location_address or 'Not specified'}
- WiFi Password: {kb.wifi_password or 'Ask staff'}
- Contact Phone: {kb.contact_phone or 'Not specified'}
- Menu Link: {kb.menu_url or 'Ask staff'}
- Reservation Link: {kb.reservation_url or 'Walk-ins welcome'}
- Payment Methods: {kb.payment_methods or 'Not specified'}
- Parking Info: {kb.parking_info or 'Not specified'}
- Dietary Options: {kb.dietary_info or 'Not specified'}
- Policy/Rules: {kb.policy_info or 'Standard restaurant rules apply'}

GUIDELINES:
- If the answer is in the context, provide it.
- If the answer is NOT in the context, apologize and suggest calling {kb.contact_phone or 'the restaurant'}.
- Do NOT make up facts.
"""

    try:
        completion = groq.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm having trouble connecting to my brain right now. Please try again."
