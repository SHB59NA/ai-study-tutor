import spaces

from demo import demo


@spaces.GPU
def zerogpu_compatibility_probe():
    """Register a minimal ZeroGPU-compatible function for Hugging Face Spaces.

    The AI Study Tutor itself uses the Gemini API and does not require local GPU
    compute. This no-op function satisfies ZeroGPU startup requirements while the
    application continues to run its normal workload on CPU.
    """
    return "ready"


if __name__ == "__main__":
    demo.launch()
