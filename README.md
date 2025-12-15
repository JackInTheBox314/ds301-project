# NYU Course RAG Planner

A Retrieval-Augmented Generation (RAG) notebook that helps plan multi-semester NYU course schedules.
It retrieves relevant courses from a catalog CSV using **Sentence-Transformers + FAISS**, then uses an **OpenAI chat model** to generate an 8-semester plan **based only on the retrieved context**.

## How it works
1. **Load course catalog** from `courses_detailed.csv`
2. **Build “course docs”** (one text block per course, plus metadata)
3. **Embed** course docs with `sentence-transformers/all-MiniLM-L6-v2`
4. **Index + retrieve** with FAISS (L2 similarity)
5. **Prompt the LLM** with:
   - strict rules (“only use course codes from context”)
   - credit-load constraints (aim ~15–16)
   - prerequisite-respecting guidance (where available in the context)
6. **Post-process** the markdown plan to replace invalid/non-catalog course codes with `-` placeholders

## Repo contents (suggested)
```txt
.
├── RAG_system (4).ipynb
├── courses_detailed.csv
└── README.md
