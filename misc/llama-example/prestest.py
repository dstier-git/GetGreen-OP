from transformers import pipeline, AutoModelForVision2Seq, AutoProcessor
import torch

model_id = "meta-llama/Llama-3.2-11B-Vision-Instruct"

# Load model in 4-bit quantized mode
model = AutoModelForVision2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.float16,             # computation dtype
    load_in_4bit=True,                     # activate 4-bit loading
    device_map="mps",                     # automatically place on GPU/CPU
)

processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    task="image-text-to-text",
    model=model,
    processor=processor,
    torch_dtype=torch.float16,
    device_map="auto",
)

messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/p-blog/candy.JPG"},
            {"type": "text", "text": "What animal is on the candy?"},
        ],
    },
]

out = pipe(messages)
print(out)
