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
Generally, the coupling between a vibrational degree of freedom (DOF) and electronic state, often referred to as electron–vibrational coupling, is related to the reorganization energy associated with the change in the vibrational equilibrium position when the electronic state changes. A typical nonadiabatic model for VCET studied in broadband pump–probe experiments is thought of as follows (7, 15): First, the system is initialized in a reactant vibronic state, which consists of an excited electronic state and a wavepacket possessing vibrational coherence on the intramolecular vibrational DOFs coupled with the electronic excitation. Then, on the same timescale as the periodic coherent motion of the wavepacket, ET also occurs, abruptly transforming the reactant vibronic state into the product vibronic state. The product vibronic state consists of a charge-transfer electronic state with weak electronic coupling to the excited electronic state and a new wavepacket whose vibrational coherence differs from that of the initial state due to the change in vibrational mode displacements (i.e. the product state as a different equilibrium geometry than the initial state).
The short, sub-100 fs, timescales of typical VCET reactions, and the drastic change in vibrational coherence within this short period pose challenges for measuring details of vibrational decoherence. For example, the vibrational coherence is lost within a few periods at most, so the conventional scheme based on a FT analysis of oscillations in pump–probe spectrum signals is difficult. It is even more challenging to use frequency-domain filtering and subsequent inverse FT analyze (1, 2, 16) to resolve decoherence times. Other work has found that directly fitting the experimental results with groups of decaying oscillation functions can be a sensitive approach to analysis (17). Nevertheless, inspired by experimental protocols, theoretical studies aim to simulate these oscillatory signals and analyze their FTs. However, as a range of powerful numerical methods (18, 19) now give access to complete electron–vibrational density matrices of the studied system and environment, it is possible to explore coherence dynamics in much greater microscopic, real-time detail, enabling new insights into the mechanisms of coherence generation, transfer, and decoherence in ultrafast processes.
Rather than trying to simulate and resolve signal oscillations, here we propose a measure based on quantum information theory that provides a direct, accurate, and insightful way to study vibrational coherence. Quantitative and easy-to-compute coherence measures, such as relative entropy (20), -norm (20), and quantum Jensen–Shannon divergence (21–23), allow vibrational coherence  to be directly measured for a vibrational system’s density matrix ρ with respect to a basis set made up of the eigenstates of the vibrational system. Thus,  for the reactant and product states can be evaluated with sufficient time resolution to study the vibrational dynamics on the required timescale of ~100 fs through these quantum information measures (QIM).
Implementing a suitable QIM requires a reliable characterization of the electron–vibrational coupled system. This characterization necessitates not only an accurate determination of the diagonal elements but also a precise evaluation of the off-diagonal elements of the density matrix describing the electron–vibrational coupled system. This requirement limits the application of quantum simulation methods that treat the vibrational DOFs classically or treat both electronic and vibrational DOFs semiclassically (24–29).
The numerically exact time-dependent density matrix renormalization group (TD-DMRG) method has been shown to be a highly accurate, efficient, and robust method for the quantum dynamics simulation of electron–vibrational coupled systems (18, 30–43).Through TD-DMRG, both vibrations and electron dynamics are simulated quantum mechanically, offering a significant advantage in accurately capturing dynamics of vibrational coherence in electron–vibrational coupled systems. The flexibility of TD-DMRG lies in its ability to control virtual bond dimension, ensuring numerical accuracy at a manageable computational cost. Furthermore, the computational cost with a fixed bond dimension scales polynomially with system size, making it scalable for large system.
In this work, we employ a combination of numerically exact TD-DMRG quantum simulations (18, 39, 44, 45) and analysis of the density matrix using quantum information measures to investigate vibrational decoherence in a typical VCET reaction between a naphthacene dye and an electron donating solvent, a system studied in recent experiments (2). We find that a quantum quench model explains the basic mechanism of the ultrafast vibrational decoherence associated with VCET. Specifically, we find that the relevant vibrations have large displacements in the reactant state, but their product equilibrium positions are closer to the geometry where the wavepackets are launched (the Franck–Condon region). We find that this abrupt vibrational decoherence is mitigated by the interplay of timescales of wavepacket motion and electron transfer.
The quantum quench model for reactive modes in VCET is expected able to explain the vibrational decoherence associated with a broader class of photophysical processes including electron transfer (4, 5, 46–52), internal conversion (53–55), intersystem crossing (56–60) and singlet fission dynamics (61) in chemical and biological systems
It is anticipated that our analysis is applicable not solely to transient absorption spectroscopy, but also to other experiments for investigating vibrational coherence, such as time-resolved fluorescence (17).
The analysis method we use, based on QIM, represents a step toward future experimental studies on vibrational decoherence assisted by quantum information measures. Although out of reach at present owing to the lack of suitable experimental measures of quantum correlations, such studies are anticipated to advance the field of quantum information science in molecular systems (62–66)."""

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
            timeout=60  # Timeout after 60 seconds
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