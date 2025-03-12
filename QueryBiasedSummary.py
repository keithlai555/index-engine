import re
import heapq
from typing import List
import BM25

TAGS = re.compile(r'<[^>]+>')
STOPS = re.compile(r'(?<=[.!?])\s+')
ESCAPES = re.compile(r'[\n\\]+')

class QueryBiasedSentence:
    def __init__(self, text: str, score: float):
        self.text = text
        self.score = score

    def __lt__(self, other):
        return self.score > other.score

def summarize(query, text, top_n: int = 3):
    text = re.sub(TAGS, '', text)
    text = re.sub(ESCAPES, ' ', text)
    sentences = re.split(STOPS, text)

    trim_sentences = [s.strip() for s in sentences if len(s.strip().split()) > 4]

    query_tokens = BM25.tokenize(query)
    heap = []

    for index, sentence in enumerate(trim_sentences):
        tokens = BM25.tokenize(sentence)

        l = 2 if index == 0 else (1 if index == 1 else 0)
        c = sum(list(tokens).count(q) for q in query_tokens)
        d = len(set(query_tokens) & set(tokens))

        k_max = 0
        k = 0
        for t in tokens:
            if t in query_tokens:
                k += 1
                k_max = max(k_max, k)
            else:
                k = 0

        score = 2 * c + 3 * d + 4 * k_max + l
        heapq.heappush(heap, QueryBiasedSentence(sentence, score))

    summary = [heapq.heappop(heap).text for _ in range(min(top_n, len(heap)))]

    final_summary = ' '.join(summary).strip()
    # collapse multiple spaces
    final_summary = re.sub(r'\s+', ' ', final_summary)

    return final_summary
