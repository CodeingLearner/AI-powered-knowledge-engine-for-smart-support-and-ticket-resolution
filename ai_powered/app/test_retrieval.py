import sys
sys.path.append("app")

import rag_engine

query = "system not working"  # change this to match words in your knowledge files

result = rag_engine.get_relevant_context(query)

print(f"KB Found      : {result['kb_context_found']}")
print(f"Retrieval     : {result['retrieval_score']}")
print(f"Matches       : {len(result['matches'])}")
print(f"\nContext Preview:\n{result['context_text'][:500]}")
