## Inspiration

In an era of misinformation, distinguishing fact from fiction has become increasingly challenging. RealityCheck was created to address this problem by providing a fast, reliable, and AI-powered fact-verification system that enables users to verify information effortlessly.

The idea for RealityCheck was inspired by an experience one of our team members, Ani, had at a Forbes 30 Under 30 event, where he spoke with a BBC anchor about accessing reliable information. When Ani asked how an average person could confidently determine the truthfulness of the news they consume, the anchor responded that it was the reader’s responsibility to research multiple sources before forming a conclusion. This conversation sparked a realization: with today's advancements in Agentic AI technology, we have the potential to automate this process, making fact-checking more accessible, efficient, and reliable for everyone.
RealityCheck aims to process claims, retrieve relevant data, and provide evidence-backed verdicts in real-time, helping users navigate the complexities of modern information consumption with confidence.

## What it does

RealityCheck is an AI-powered fact-verification system designed to help users quickly assess the accuracy of claims. It retrieves relevant information from trusted sources, analyzes the data using advanced AI models, and delivers a clear, evidence-backed verdict. By providing reliable and explainable fact-checking, RealityCheck aims to combat misinformation and empower users with the truth.

## How we built it

RealityCheck is built using a combination of AWS services and AI models to deliver fast and reliable fact verification.

AI Agents: We leverage four AI agents for key tasks: chunking/decomposition, search, summarization, and sentiment analysis.
Data Storage: Pre-embedded factual data is securely stored in Amazon S3.
Vector Search: Amazon OpenSearch with vector search capabilities efficiently indexes and retrieves relevant information.
AI Processing: Amazon Bedrock powers the LLM responsible for analyzing retrieved data and generating verification results, we also used the Gemini API and Ollama models for Agentic AI workflows and text summarization.
Backend Services:  Using Python’s FastAPI, we handle requests and manage data flow.
Frontend Interface: A Next.js-based web app provides an intuitive interface for users to submit claims and view fact-checking results.

## Challenges we ran into

- Latency Optimization: Ensuring fast data retrieval and LLM inference was critical to achieving real-time fact verification.
- Credibility Scoring: We implemented a system to dynamically evaluate the reliability of retrieved sources.
- Agentic AI Learning Curve: None of us had prior experience with the Agentic AI framework, but we took on the challenge of building this app with a complex architecture.
- Handling AI Hallucinations: One of our biggest challenges was mitigating hallucinations and unpredictable AI outputs. We struggled to get consistently formatted JSON outputs from the AI models, which required significant debugging and fine-tuning.
- New Tech Stack: Hosting our application on Cloudflare and AWS cloud services was a new experience, and we faced several technical challenges along the way.

## Accomplishments that we're proud of
- Successfully integrated pre-embedded data with Amazon Bedrock, eliminating redundant processing.
- Enhanced retrieval accuracy by implementing efficient vector search with Ollama.
- Built a fully functional Retrieval-Augmented Generation (RAG) pipeline using CrewAI, improving fact verification reliability. 
- At last, we were very proud of taking the first step in building this app which has the potential of helping so many people.

## What we learned

- Leveraging Amazon Bedrock and OpenSearch to build scalable AI-driven retrieval systems.
- Optimizing LLM performance for fact-checking applications.
- Developing techniques to rank and evaluate the credibility of retrieved information.

## What's next for RealityCheck

- Expanding to multi-modal fact verification, incorporating image and video analysis.
- Enhancing retrieval efficiency using hybrid search methods (combining semantic and keyword-based approaches).
- Deploying a real-time misinformation tracking system for news and social media.
- Introducing user feedback mechanisms to continuously improve verification accuracy.
