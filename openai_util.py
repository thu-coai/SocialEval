from openai import OpenAI

# Initialize the client
client = OpenAI(
    api_key="sk-jBKKpw1tPxz7zX9962F886Fa222f41E8AbF800D273B22a17",
    base_url="http://115.182.62.174:18888/v1"
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