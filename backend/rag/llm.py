import subprocess


def generate_answer(prompt: str):
    """
    Send a prompt to the local Ollama model
    and return the generated answer.
    """

    result = subprocess.run(
        ["ollama", "run", "llama3.2", prompt],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Ollama error: {result.stderr}"
        )

    return result.stdout.strip()


if __name__ == "__main__":

    prompt = "Explain Retrieval-Augmented Generation in simple words."

    answer = generate_answer(prompt)

    print("\nGenerated answer:\n")
    print(answer)