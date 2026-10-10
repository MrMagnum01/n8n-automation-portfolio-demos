# RAG knowledge base: ask questions of company documents, get answers with sources (n8n + local Ollama)

## 60-second write-up

**Problem.** Teams have policies, manuals and FAQs scattered across PDFs/docs, and people ask the same questions
repeatedly. A chatbot that guesses is worse than none: it must answer only from the documents, say *which* document
and section it used, and say "not in the documents" when the answer is not there.

**What it does.** Two n8n workflows:
1. **Ingest** reads 12 documents, splits them into 60 section chunks (each with a document id and chunk id such as
   `meridian-pto-policy#carryover`), embeds each chunk with a local embedding model (`all-minilm:33m`, 384 dims) and saves the vector index to a JSON file.
2. **Ask** (a Webhook `POST /webhook/rag-ask` and a Manual Trigger with 7 fixed test questions) embeds the question, retrieves the top 4 chunks
   by cosine similarity, and has a local `qwen2.5:1.5b-instruct` answer **only** from those chunks. The answer must cite chunk ids.
   A Code node then checks every cited id against the chunks that were actually in the prompt; an answer with no valid citation
   is turned into an abstention. Output: answer + citations + retrieved chunks + latency.

**Result (real run, execution 14; 7 questions: 5 answerable, 2 not in the documents).** Scored by rule, not by an LLM:
- **5 of 5** answerable questions were answered with the expected *document* cited (the expected fact string also appeared in all 5 answers).
  Stricter, chunk-level: **4 of 5** cited the exact expected section (T2 gave the right answer but cited `cascade-pos-manual#support-contact` instead of `#error-codes`, same document).
- **2 of 2** unanswerable questions were correctly answered "Not in the documents." (0 false abstentions on the answerable ones).
- **Latency** (embedding + generation, as reported by Ollama, CPU only, Xeon Silver 4114): median **8.8 s**, min 2.1 s, max 17.7 s per question for the batch run.
  Via the webhook with a warm model: 2.2 s and 3.2 s (HTTP wall 2.5 s / 3.4 s). **Caveat:** the box was shared with other jobs (load average about 10 on 20 threads) during the runs, so these numbers are noisy and likely pessimistic.
- **Cost: $0 metered.** Both models run locally in Ollama; no paid API and no external network call.

Sample size is 7 questions on a synthetic corpus. These numbers show that the pipeline works end to end; they are not a general accuracy claim.
A 1.5B model is small: it can cite the wrong section (T2) or pad an answer with a neighbouring sentence (T4). For production the same workflow works with a larger local model or a hosted one by changing one URL/model name.

## Screenshots
- `screenshots/01-ingest-canvas.png`, `screenshots/02-ask-canvas.png`: the two workflows
- `screenshots/03-ask-execution-success.png`: successful execution #14 (7 items through every node)
- `screenshots/04-answers-with-citations.png`: the answers with citations (rendered from `output/answers.json`)

## How to run
Prerequisites: n8n 2.x, Ollama on `127.0.0.1:11434` with `all-minilm:33m` and `qwen2.5:1.5b-instruct` pulled.
1. Copy `sample-data/docs/*.md` to `~/.n8n-files/rag-knowledge-base/docs/` (the folder n8n's file nodes may read/write; inside the Docker container this is `/home/node/.n8n-files/...`).
2. Import: `n8n import:workflow --input=workflow-ingest.json` and `--input=workflow-ask.json` (`workflow.json` is both in one array).
3. Run **RAG KB - 1 Ingest** (Execute workflow) once. It writes `index.json`.
4. Run **RAG KB - 2 Ask** with the Manual Trigger: it answers the 7 test questions and writes `output/answers.json` and `output/answers.md`.
5. Or publish/activate **Ask** and call it:
   `curl -X POST http://127.0.0.1:5678/webhook/rag-ask -H 'Content-Type: application/json' -d '{"question":"How many unused PTO days can be carried over?"}'`

Note: `n8n execute` from the CLI collides with the running instance's task-runner port when the workflow has Code nodes, so the runs here were started through n8n's own editor REST endpoint (`tools/n8n_run.py`), which is the same as pressing "Execute workflow".

## Why not the built-in LangChain vector store nodes
I did not use them, and I did not test them. The deliberate choice was a plain JSON index on disk plus cosine similarity in a Code node:
- The in-memory vector store lives inside the n8n process and is lost on restart; the ingest and ask runs would have to share one process and re-ingest after every restart. A JSON file survives restarts and is inspectable (`output/vector-index.json`).
- Citation ids, status metadata (current vs. superseded) and a code-level check that every citation really was in the prompt are explicit and testable here.
- For 60 chunks, brute-force cosine is instant. For thousands of documents you would swap the JSON file for a real vector store (Qdrant, pgvector), which n8n has nodes for.

## Nodes
**Ingest:** Manual Trigger, Read Docs (Read/Write Files), Extract Text, Chunk Documents (Code: front-matter + split on `## ` sections, id = `doc#section-slug`), Embed Chunk (HTTP Request to Ollama `/api/embed`), Build Vector Index (Code), To JSON File, Write index.json, Ingest Summary.
**Ask:** Manual Trigger and Webhook, Load Index, Extract Index, Prepare Questions (Code: webhook question or the fixed test set), Embed Question (HTTP), Retrieve Top-k (Code: cosine, prompt build), Generate Answer (HTTP to Ollama `/api/chat`, JSON-schema constrained output, temperature 0), Parse and Verify Citations (Code), Is Webhook Call? (IF), then either Shape Reply + Respond to Webhook, or Score and Build Report (Code, rule-based scoring) + two Convert to File + two Write Files.

## What is mocked
Nothing is mocked: real local models, real files, a real webhook. The "company" documents are synthetic (see below).

## Scoring rules (no LLM judge)
- Answerable question: correct if status is ANSWER and at least one cited chunk belongs to the expected document id. Chunk-level: the exact expected chunk id is cited.
- Unanswerable question: correct if status is ABSTAIN.
- Also reported: expected chunk in top-4 retrieval (5/5), expected fact string present in the answer (5/5).
- Test set: 5 answerable (incl. two "current vs. superseded version" questions where the older policy document is also in the index) and 2 unanswerable questions, taken from the sibling `local-document-qa` evaluation questions.

## Honest notes on the build
- The first full run scored 4/5: the model copied the placeholder id from my prompt example (`some-doc#some-section`) as its citation for T2, which the citation check correctly turned into an abstention. I removed the example from the prompt (a prompt bug, not a tuning to the questions) and re-ran. Runs: executions 5, 7 (first prompt) and 8, 14 (fixed prompt). The questions were not frozen before the first run and there was only this one prompt fix.
- Across the two fixed-prompt runs T2 cited the wrong section of the right document both times.
- The Ask workflow is left published so the webhook answers on `127.0.0.1:5678` (loopback only).

## Cost per run
Measured: **$0 metered** (local Ollama models, no paid API). The only cost is local CPU time (about 18 s of wall clock for the 7 questions here).

## Licences
| Component | Licence |
|---|---|
| n8n 2.42 | Sustainable Use License (source-available, not OSI-approved) |
| Ollama | MIT |
| qwen2.5:1.5b-instruct weights | Apache-2.0 |
| all-minilm:33m (all-MiniLM-L6-v2) weights | Apache-2.0 |
| Helper scripts in `tools/` (Python stdlib; puppeteer-core for screenshots) | puppeteer-core Apache-2.0 |
| Synthetic documents | written for the sibling `local-document-qa` demo, copied unmodified |

## Synthetic data, no client work
All 12 documents in `sample-data/docs/` are fictional (three made-up companies: Solstice Systems, Meridian Health Partners, Cascade Retail Co). No real company, person, customer or client document was used.

## Folder
`workflow.json`, `workflow-ingest.json`, `workflow-ask.json` (exports, no credentials), `sample-data/docs/`, `output/` (`answers.json`, `answers.md`, `answers.html`, `webhook-examples.jsonl`, `vector-index.json`), `screenshots/`, `tools/` (`build_workflows.py`, `n8n_run.py`, `render_answers_html.py`, `screenshots.mjs`), `RUN-EVIDENCE.md`.
