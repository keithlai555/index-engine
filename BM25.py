import argparse
import json
import sys
import os
import sys
import math

from PorterStemmer import PorterStemmer

# bm25 hyperparameters
k_1 = 1.2
b = 0.75

def write_to_results_file(output_directory, top_ranked_documents):
    with open(output_directory + "/hw4-bm25-baseline-k34lai.txt", 'a') as results_file:
        results_file.write(top_ranked_documents + "\n")
            
def calculate_BM25_algorithm(inverted_index, lexicon, docnos, query_tokens, stem, doc_lengths, average_doc_length):
    BM25_scores = {}
    porterStemmer = PorterStemmer()
    N = len(docnos)

    for query_token in query_tokens:
        if stem:
            query_token = porterStemmer.stem(query_token, 0, len(query_token) - 1)
        if query_token not in lexicon:
            continue

        query_token_id = lexicon[query_token]
        doc_postings = inverted_index[query_token_id]

        # count number of docs in collection with query token in them
        n_i = len(doc_postings[::2])
        idf = math.log((N - n_i + 0.5) / (n_i + 0.5))

        for index in range(0, len(doc_postings), 2):
            doc_id = doc_postings[index]
            doc_no = docnos[doc_id]
            f_i = doc_postings[index + 1]
            doc_length = doc_lengths[doc_id]
            K = k_1 * ((1 - b) + b * (doc_length / average_doc_length))
            tf = f_i / (K + f_i)
            BM25_score = tf * idf

            # update scores in dictionary
            if doc_no in BM25_scores:
                BM25_scores[doc_no] = BM25_scores[doc_no] + BM25_score
            else:
                BM25_scores[doc_no] = BM25_score

    sorted_BM25_scores = dict(sorted(BM25_scores.items(), key=lambda item: item[1], reverse=True))

    return sorted_BM25_scores

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

def get_queries(directory_path):
    queries_file_path = directory_path + "/queries.txt"
    
    if os.path.exists(queries_file_path):
        with open(queries_file_path, 'r') as queries_file:
            queries = queries_file.read()
    else:
        print("Unable to find queries file!")
        sys.exit()

    return queries

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

# added for problem 7E part b bonus mark
def BM25_parameter_optimization(inverted_index, lexicon, docnos, queries, doc_lengths, average_doc_length, stem, directory_path):
    k1_values = [1.0, 1.2, 1.4, 1.6, 1.8]
    b_values = [0.0, 0.5, 1.0]

    global k_1, b
    i = 0

    for k1 in k1_values:
        for b_value in b_values:
            i += 1
            k_1, b = k1, b_value
            output_file = directory_path + f"/bm25-run-{i}-k34lai.txt"
            with open(output_file, 'w') as output_file:
                for index in range(0, len(queries), 2):
                    query_tokens = tokenize(queries[index + 1])
                    topic_id = queries[index]

                    ranked_documents_dict = calculate_BM25_algorithm(inverted_index, lexicon, docnos, query_tokens, stem, doc_lengths, average_doc_length)

                    top_1000_documents = list(ranked_documents_dict.items())[:1000]
                    
                    for index, (doc_no, score) in enumerate(top_1000_documents):
                        output_file.write(f"{topic_id} Q0 {doc_no} {index + 1} {score} k34laiBM25run-{i}\n")

def main():
    # program arguments
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--directory_path', required=True, help='Directory path')
    parser.add_argument('--stem', required=True, help='Boolean true or false for whether to stem the words')
    
    cli = parser.parse_args()
    directory_path = cli.directory_path
    stem = cli.stem
    stem = stem.lower() == "true"

    # make output directory if it doesn't exist
    if not os.path.exists(directory_path):
        print("This directory path does not exist! Please enter an existing directory path!")
        sys.exit()

    inverted_index = get_inverted_index(directory_path)
    queries = get_queries(directory_path)
    lexicon = get_lexicon(directory_path)
    docnos = get_docnos(directory_path)
    doc_lengths = get_doc_lengths(directory_path)

    # for finding the number of cells that are filled for problem 5
    # total_sum = 0
    # for key, value in inverted_index.items():
    #     total_sum += len(value)
    # print(total_sum / 2)

    average_doc_length = 0

    if len(doc_lengths) > 0:
        average_doc_length = sum(doc_lengths) / len(doc_lengths)

    if stem:
        output_file = directory_path + "/hw4-bm25-stem-k34lai.txt"
        name = "k34laiBM25stem"
    else:
        output_file = directory_path + "/hw4-bm25-baseline-k34lai.txt"
        name = "k34laiBM25baseline"

    # split each query into its own line
    queries = queries.splitlines()
    docnos = docnos.splitlines()

    # code for optimizing parameter by performing hyperparameter sweep
    # BM25_parameter_optimization(inverted_index, lexicon, docnos, queries, doc_lengths, average_doc_length, stem, directory_path)

    with open(output_file, 'w') as output_file:
        for index in range(0, len(queries), 2):
            query_tokens = tokenize(queries[index + 1])
            topic_id = queries[index]

            ranked_documents_dict = calculate_BM25_algorithm(inverted_index, lexicon, docnos, query_tokens, stem, doc_lengths, average_doc_length)

            top_1000_documents = list(ranked_documents_dict.items())[:1000]
            
            for index, (doc_no, score) in enumerate(top_1000_documents):
                output_file.write(f"{topic_id} Q0 {doc_no} {index + 1} {score} {name}\n")

if __name__ == '__main__':
    main()
