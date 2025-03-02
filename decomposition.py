import subprocess
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re

app = FastAPI()

class ArticleRequest(BaseModel):
    article: str

PROMPT = "Analyze the given article and extract complete, self-contained sentences or chunks that make factual claims, assertions, or statements requiring verification. Ensure that each extracted chunk has enough context to be meaningfully checked against external sources. Do not provide any explanations or summaries—only return the extracted statements that require fact-checking."

ARTICLE_TEXT = """In recent years, vibrational decoherence has been widely measured using broadband pump–probe spectroscopy techniques to study the role of vibrations in photoinduced ultrafast vibration-coupled electron transfer (1–5) (VCET). VCET is a regime of ultrafast electron transfer where the intramolecular vibrational coordinate plays a key role; oftentimes VCET is prominent in the Marcus inverted regime (6–12). Recent experiments based on wavepacket spectroscopies, such as broad-band pump–probe, have used vibrational decoherence to detect vibrations associated with the reaction coordinate (13). A wavepacket is a superposition of the vibrational eigenstates for the system. Coherence refers to the necessary locking of eigenstate phases. The property vibrational decoherence quantifies the loss of this coherence, usually described as wavepacket dispersion. Vibrational coherence is usually measured from the frequency-resolved Fourier transformation (FT) signal of time-resolved pump–probe spectroscopy signals. The loss in intensity at the vibrational frequency between reactant and product state is an indication of vibrational decoherence.
Vibrational decoherence during the transition from reactant to product states in electron transfer (ET) is considered to be an indication for the role of that vibration in the reaction coordinate. While that interpretation is intuitive, it has not yet been supported by a general theoretical model that explains the mechanism of decoherence. This is surprising, because one would think the result would be obvious. It follows that a general theoretical foundation for analyzing these data is lacking. In this work, we examine how VCET can cause vibrational decoherence. We find that the explanation is similar to a quantum quench event (14) on the timescale of ~100 fs. That is, an abrupt change in equilibrium geometry from reactant to product states can lead to rapid vibrational decoherence, even under unitary evolution. Owing to the quantum quench, the vibrational coherence may change drastically within a timescale of ~100 fs, even without solvent interplay.
"""

def call_ollama(prompt: str) -> str:
    command = ["ollama", "run", "llama3.2:latest"]
    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            timeout=60,
            encoding="utf-8"
        )
        end_time = time.time()
        print(f"✅ Ollama execution completed in {end_time - start_time:.2f} seconds")
        return result.stdout
    except subprocess.TimeoutExpired:
        print("⚠️ Ollama timed out! Try using a shorter input or a lighter model.")
        raise Exception("Ollama took too long to respond. Please try again with a shorter input or a lighter model.")
    except subprocess.CalledProcessError as e:
        print("❌ Ollama call error:", e.stderr)
        raise Exception(f"Ollama call error: {e.stderr}")

def extract_chunks(article_text: str) -> list:
    full_prompt = f"{PROMPT}\n\nArticle:\n{article_text}"
    response = call_ollama(full_prompt)
    
    chunks = []
    for line in response.splitlines():
        cleaned_line = line.strip()
        if cleaned_line:
            chunks.append(cleaned_line)
    
    return chunks

def main():
    chunks = extract_chunks(ARTICLE_TEXT)
    print("Extracted Chunks:", chunks)

if __name__ == '__main__':
    main()