# Run evidence

Environment: n8n 2.42.6 in Docker (loopback only), Ollama local, `all-minilm:33m` + `qwen2.5:1.5b-instruct`, CPU only (Xeon Silver 4114, 20 threads, shared with other jobs; load average about 10 during the runs).
Runs were started via the editor REST endpoint (`tools/n8n_run.py`), credentials from the secret store environment, never written anywhere.

## Executions (from n8n, UTC, 2026-10-10)
| Exec | Workflow | Mode | Status | Started | Stopped | Note |
|---|---|---|---|---|---|---|
| 2 | RAG KB - 1 Ingest | manual | success | 11:14:14.5 | 11:14:18.0 | first ingest: 12 docs, 60 chunks, dim 384 |
| 3 | RAG KB - 2 Ask | manual | error | 11:14:22 | 11:14:22 | my bug: Extract From JSON needed a destination key; fixed |
| 5 | RAG KB - 2 Ask | manual | success | 11:14:39 | 11:15:18 | first prompt: 4/5 + 2/2 (T2 forced abstain, see README) |
| 7 | RAG KB - 2 Ask | manual | success | 11:15:35 | 11:15:52 | first prompt, re-run: 4/5 + 2/2 |
| 8 | RAG KB - 2 Ask | manual | success | 11:16:07 | 11:16:42 | fixed prompt: 5/5 + 2/2 (load avg 12, slow) |
| 9, 11, 12 | RAG KB - 2 Ask | webhook | success | 11:16:50 / 11:17:04 / 11:17:06 | | `POST /webhook/rag-ask` (11, 12 saved in `output/webhook-examples.jsonl`) |
| 13 | RAG KB - 1 Ingest | manual | success | 11:17:14.7 | 11:17:17.0 | final ingest (`output/vector-index.json`) |
| **14** | RAG KB - 2 Ask | manual | **success** | 11:17:19.4 | 11:17:37.8 | **final run, output in `output/`, screenshot 03** |

## Final run summary (`output/answers.json` -> `summary`)
```
questions 7, answerable 5, answered_with_correct_doc_citation 5, answered_with_correct_chunk_citation 4,
expected_chunk_in_top_k 5, expected_fact_string_in_answer 5, should_abstain 2, abstained_correctly 2,
false_abstentions_on_answerable 0, latency_s_per_question {min 2.08, median 8.79, max 17.7, mean 9.62}
```
Per question (id, status, latency s, cited): T1 ANSWER 2.08 `meridian-pto-policy#carryover`; T2 ANSWER 4.37 `cascade-pos-manual#support-contact` (right doc, wrong section);
T3 ANSWER 17.7 `solstice-backup-manual#encryption`; T4 ANSWER 7.71 `meridian-remote-work-v2#equipment`; T5 ANSWER 15.58 `cascade-returns-policy-v2#return-window`, `#exceptions`;
T6 ABSTAIN 8.79; T7 ABSTAIN 11.1.

## Webhook example (execution 11, warm model)
```
POST /webhook/rag-ask {"question":"How many weeks of paid parental leave does Meridian give the primary caregiver?"}
-> status ANSWER, "Meridian offers 12 weeks of paid parental leave for the primary caregiver. [meridian-hr-faq#parental-leave]", latency_s 2.2 (HTTP wall 2.47 s)
POST ... {"question":"Does Cascade Retail Co ship orders internationally?"} -> status ABSTAIN, "Not in the documents.", latency_s 3.16
```

## Notes
- Paths such as `/home/node/.n8n-files/rag-knowledge-base/...` in the workflow JSON are the container-side locations n8n is allowed to read/write; unavoidable.
- Metered spend: $0 (no external network calls; Ollama on loopback).
