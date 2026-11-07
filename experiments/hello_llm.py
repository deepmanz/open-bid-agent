import ollama

# The role statement: tells the model whose side it is on
SYSTEM_PROMPT = (
    "You are an experienced bid manager at an IT services company "
    "that responds to client RFPs. Always answer from the vendor's point of view."
)

response = ollama.chat(
    model="llama3.1:8b",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "In 3 lines, how do you decide whether to bid on an RFP?"},
    ],
)

print(response["message"]["content"])