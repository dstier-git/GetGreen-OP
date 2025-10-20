import transformers
import torch
import platform

model_id = "meta-llama/Llama-3.2-1B"

# Check if running on Apple Silicon OR if MPS is available
is_apple_silicon = (
    (platform.machine() == "arm64" and platform.system() == "Darwin") or
    (torch.backends.mps.is_available() and platform.system() == "Darwin")
)

if is_apple_silicon:
    # For Apple Silicon, use CPU with float16
    # MPS doesn't support bfloat16, and the model has bfloat16 weights
    dtype = torch.float16
    device_map = "cpu"  # Force CPU usage
    print("Detected Apple Silicon - using float16 on CPU")
else:
    # Use bfloat16 for other platforms with auto device mapping
    dtype = torch.bfloat16
    device_map = "auto"
    print("Using bfloat16 with auto device mapping")

pipeline = transformers.pipeline(
    "text-generation", 
    model=model_id, 
    model_kwargs={"dtype": dtype},
    device_map=device_map
)

result = pipeline("Hey how are you doing today?", max_new_tokens=50)
print(result)