import BM25
import QueryBiasedSummary
import sys
import os
import time
import json
import re

DIRECTORY_PATH = '/searchengines/latimes-index'
VALID_INPUTS = ['N', 'Q']

def get_inverted_index(directory_path):
    inverted_index_file_path = directory_path + "/inverted-index.json"

    if os.path.exists(inverted_index_file_path): 
        with open(inverted_index_file_path, 'r') as inverted_index_file:
            inverted_index = json.load(inverted_index_file)
    else:
        print("Unable to find the inverted index file!")
        sys.exit()

    inverted_index = {int(index): postings for index, postings in inverted_index.items()}
    return inverted_index

def get_lexicon(directory_path):
    lexicon_file_path = directory_path + "/lexicon.json"

    if os.path.exists(lexicon_file_path): 
        with open(lexicon_file_path, 'r') as lexicon_file:
            lexicon = json.load(lexicon_file)
    else:
        print("Unable to find the lexicon file!")
        sys.exit()

    return lexicon

def get_docnos(directory_path):
    docnos_file_path = directory_path + "/docnos.txt"

    if os.path.exists(docnos_file_path): 
        with open(docnos_file_path, 'r') as docnos_file:
            docnos = docnos_file.read()
    else:
        print("Unable to find the docnos file!")
        sys.exit()

    return docnos

def get_doc_lengths(directory_path):
    doc_lengths_file_path = directory_path + "/doc-lengths.txt"
    doc_lengths = []

    if os.path.exists(doc_lengths_file_path): 
        with open(doc_lengths_file_path, 'r') as doc_lengths_file:
            for line in doc_lengths_file:
                doc_lengths.append(int(line.strip()))
    else:
        print("Unable to find the doc-lengths file!")
        sys.exit()

    return doc_lengths

def tokenize(text):
    text = text.lower() 
    tokens = set()

    start = 0 
    i = 0

    for currChar in text:
        if not currChar.isdigit() and not currChar.isalpha() :
            if start != i :
                token = text[start:i]
                tokens.add(token)
                
            start = i + 1

        i = i + 1

    if start != i :
        tokens.add(text[start:i])

    return tokens

def query_results(query, inverted_index, lexicon, docnos, doc_lengths, average_doc_length):
    start = time.time()
    rank_doc_no = {}
    query_tokens = tokenize(query)

    ranked_documents_dict = BM25.calculate_BM25_algorithm(inverted_index, lexicon, docnos, query_tokens, False, doc_lengths, average_doc_length)

    limit = min(len(ranked_documents_dict), 10)
    i = 1

    for doc_no, score in ranked_documents_dict.items():
        yy = doc_no[6:8]
        mm = doc_no[2:4]
        dd = doc_no[4:6]
        document_file_path = DIRECTORY_PATH + f"/{yy}/{mm}/{dd}/{doc_no}.txt"
        document_metadata_file_path = DIRECTORY_PATH + f"/{yy}/{mm}/{dd}/{doc_no}.json"
        with open(document_file_path, 'r') as document_file:
            document = document_file.read() 
        with open(document_metadata_file_path, 'r') as metadata_file:
            metadata = json.load(metadata_file)

        text = re.search(r'<TEXT>(.*?)</TEXT>', document, re.DOTALL)
        text_content = ""
        if text:
            text_content = text.group(1).strip()
        else:
            print("No content between text tags")

        summary = QueryBiasedSummary.summarize(query, text_content)
        headline = ""
        if not metadata['headline']:
            headline = "{}...".format(summary[:50])
        else:
            headline = metadata['headline']
        print("{}. {} ({})".format(i, headline.replace('\n', ''), metadata['date']))
        print("{} ({})\n".format(summary, doc_no))
        rank_doc_no[i] = doc_no
        i += 1
        if i > limit:
            break

    stop = time.time()
    print("Retrieval took {:.3f} seconds".format(stop - start))
    return rank_doc_no

def query_program(inverted_index, lexicon, docnos, doc_lengths, average_doc_length):
    query = input("Enter a query: ")
    prompt = ''

    rankings = query_results(query, inverted_index, lexicon, docnos, doc_lengths, average_doc_length)

    while prompt not in VALID_INPUTS:
        prompt = input("Enter rank of a document to view, \'N\' for a new query or \'Q\' to quit the program: ")

        if prompt == 'Q':
            print("Quitting program")
            exit()

        if prompt == 'N':
            query_program(inverted_index, lexicon, docnos, doc_lengths, average_doc_length)

        try:
            rank = int(prompt)
            if len(rankings) >= rank > 0:
                doc_no = rankings[rank]
                yy = doc_no[6:8]
                mm = doc_no[2:4]
                dd = doc_no[4:6]
                document_file_path = DIRECTORY_PATH + f"/{yy}/{mm}/{dd}/{doc_no}.txt"
                with open(document_file_path, 'r') as document_file:
                    document = document_file.read() 
                print(doc_no)
                print(document)
            else:
                print("Invalid rank entered. Please try again!")
    
        except ValueError:
            print("Invalid response. Please try again!")
            pass

def main():
    inverted_index = get_inverted_index(DIRECTORY_PATH)
    lexicon = get_lexicon(DIRECTORY_PATH)
    docnos = get_docnos(DIRECTORY_PATH)
    doc_lengths = get_doc_lengths(DIRECTORY_PATH)
    docnos = docnos.splitlines()

    average_doc_length = 0

    if len(doc_lengths) > 0:
        average_doc_length = sum(doc_lengths) / len(doc_lengths)

    query_program(inverted_index, lexicon, docnos, doc_lengths, average_doc_length)

if __name__=="__main__":
    main()