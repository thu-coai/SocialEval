from openai import OpenAI

# Initialize the client
client = OpenAI(
    api_key="xxx",
    base_url="xxx"
)


def gpt_call(prompt, model="gpt-4o"):
    """Make a call to the GPT API using the new OpenAI client."""
    response = client.chat.completions.create(
        model=model,
        temperature=1,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content