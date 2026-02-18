# RAG Evaluation Metrics

This document defines clear metrics your team can report during the project
presentation and how to measure them.

## 1) Retrieval Quality

**Goal:** check if the retriever finds the right document chunks.

- **Recall@K**: percentage of questions where at least one of the top-K chunks
  contains the correct answer.
- **MRR (Mean Reciprocal Rank)**: how high the first relevant chunk appears.

**How to use:**
1. Create a small evaluation set of Q&A pairs (e.g., 30–50 questions).
2. For each question, note the document + page that contains the answer.
3. Run retrieval and check if the correct source appears in the top-K list.
4. Compute Recall@K and MRR with a simple spreadsheet.

## 2) Answer Quality

**Goal:** check if the final answer is correct, clear, and complete.

Use a human evaluation rubric (0–2 scale):
- **2** = correct and complete
- **1** = partially correct or missing details
- **0** = incorrect or hallucinated

**How to use:**
1. Ask the same evaluation questions.
2. Have 2 team members score answers independently.
3. Average the scores and report the mean.

## 3) Faithfulness / Groundedness

**Goal:** ensure answers are supported by retrieved context.

**Metric:** % of answers where every key claim is supported by sources.

**How to use:**
1. For each answer, check if the cited sources contain the key facts.
2. Mark as **grounded** or **not grounded**.
3. Report the grounded percentage.

## 4) Fallback Rate

**Goal:** track how often the system says "I’m not sure".

**Metric:** % of user questions that trigger the human fallback response.

**How to use:**
- Count fallback responses / total questions.

## 5) Latency

**Goal:** measure responsiveness.

**Metric:** average time from user question → final response.

**How to use:**
- Time 20–30 questions and compute the average in seconds.

## Suggested Reporting Table

| Metric | Value | Notes |
| ------ | ----- | ----- |
| Recall@4 |  | retrieval effectiveness |
| MRR |  | rank of first relevant chunk |
| Answer Quality (0–2) |  | human rubric |
| Groundedness % |  | citation support |
| Fallback Rate % |  | uncertainty handling |
| Latency (sec) |  | average response time |
