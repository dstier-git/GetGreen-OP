import requests, json

# prompt = r"Format your response as a one paragraph text message. Skip right to the information. Question: OMG it’s hot today! Is there any way I can cool my apartment without blasting the AC?"
prompt = (
    "Respond like a friendly, helpful person—"
    "use natural sentences, but no prefixes like 'A:' or 'Answer:'. Format the response into one paragraph."
    "It’s hot today—what are some easy ways to cool my apartment without blasting the AC?"
)

with requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.2-11b-instruct-local", "prompt": prompt, "options": {"num_predict": 100}},
    stream=True,
) as r:
    for line in r.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            print(data.get("response", ""), end="", flush=True)
