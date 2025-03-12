import argparse
import sys
from parsers import QrelsParser, ResultsParser
import os
import sys
import math
import csv

# Author: Nimesh Ghelani based on code by Mark D. Smucker

# This code doesn't do much other than sort of show how the 
# various classes can be used.

def calculate_metrics(qrel, results):
    average_precision = {}
    precision_at_10 = {}
    ndcg_at_10 = {}
    ndcg_at_1000 = {}

    # get query_ids and sort them in ascending order
    query_ids = sorted(qrel.get_query_ids())

    # iterate through every query_id
    for query_id in query_ids:
        # initialize calcution variables
        relevant_amount = 0.0
        relevant_at_10 = 0.0
        precisions = []
        dcg_at_10 = 0.0
        dcg_at_1000 = 0.0
        idcg_at_10 = 0.0
        idcg_at_1000 = 0.0
        
        query_result = results[1].get_result(query_id)

        # check if query_result has any results, if not, go to next query_id
        if not query_result:
            sys.stderr.write(query_id+' has no results, but it exists in the qrels.\n')
            average_precision[query_id] = 0.0
            precision_at_10[query_id] = 0.0
            ndcg_at_10[query_id] = 0.0
            ndcg_at_1000[query_id] = 0.0
            continue

        query_result = sorted(query_result)

        # loop through all of query results or only the first 1000 results
        for index in range(min(1000, len(query_result))):
            relevance = float(qrel.get_relevance(query_id, query_result[index].doc_id))

            # get qrels relevant docs and sort them based on relevance for ideal relevance
            relevant_docs_qrels = [(doc_id, qrel.get_relevance(query_id, doc_id))
                         for doc_id in qrel.query_2_reldoc_nos[query_id]]
            sorted_relevant_docs_qrels = sorted(relevant_docs_qrels, key=lambda x: x[1], reverse=True)

            ideal_relevance = 0
            # ensure index is valid
            if index < len(sorted_relevant_docs_qrels):
                ideal_relevance = sorted_relevant_docs_qrels[index][1]

            # make calculations for measures
            if relevance > 0:
                relevant_amount += 1.0
                current_precision = float(relevant_amount / (index + 1))
                precisions.append(current_precision)
                dcg_at_1000 += 1 / math.log2(index + 2)
            
            if ideal_relevance > 0:
                idcg_at_1000 += ideal_relevance / math.log2(index + 2)

            if index == 9:
                relevant_at_10 = relevant_amount
                dcg_at_10 = dcg_at_1000
                idcg_at_10 = idcg_at_1000

        if precisions:
            average_precision[query_id] = float(sum(precisions) / len(qrel.query_2_reldoc_nos[query_id]))
        else:
            average_precision[query_id] = 0.0

        precision_at_10[query_id] = float(relevant_at_10 / min(10, len(query_result)))

        if idcg_at_10 > 0:
            ndcg_at_10[query_id] = dcg_at_10 / idcg_at_10
        else:
            ndcg_at_10[query_id] = 0.0

        if idcg_at_1000 > 0:
            ndcg_at_1000[query_id] = dcg_at_1000 / idcg_at_1000
        else:
            ndcg_at_1000[query_id] = 0.0

    return { "average_precision": average_precision,
             "precision_at_10": precision_at_10,
             "ndcg_at_10": ndcg_at_10,
             "ndcg_at_1000": ndcg_at_1000
    }

def write_measures_to_csv(name, output_directory, measures):
    with open(os.path.join(output_directory, f'{name}.csv'), 'w', newline='') as csvfile:
        fieldNames = ['measure', 'query_id', 'score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldNames)
        writer.writeheader()
        for key, measure in measures.items():
            for query, score in measure.items():
                writer.writerow({'measure': key, 'query_id': query, 'score': f"{score:.3f}"})
            
def write_average_measures_to_csv(name, output_directory, measures):
    with open(output_directory + "/average_measures.csv", 'a', newline='') as csvfile:
        fieldNames = ['Run Name', 'Mean Average Precision', 'Mean P@10', 'Mean NDCG@10', 'Mean NDCG@1000']
        writer = csv.DictWriter(csvfile, fieldnames=fieldNames)

        mean_average_precision = float(calculate_mean(measures['average_precision']))
        mean_precision_at_10 = calculate_mean(measures['precision_at_10'])
        mean_ndcg_at_10 = calculate_mean(measures['ndcg_at_10'])
        mean_ndcg_at_1000 = calculate_mean(measures['ndcg_at_1000'])
        writer.writerow({"Run Name": name,
                         "Mean Average Precision": f"{mean_average_precision:.3f}",
                         "Mean P@10": f"{mean_precision_at_10:.3f}",
                         "Mean NDCG@10": f"{mean_ndcg_at_10:.3f}",
                         "Mean NDCG@1000": f"{mean_ndcg_at_1000:.3f}"
        })

def calculate_mean(measures_dict):
    if len(measures_dict) == 0:
        return 0.0
    return float(sum(measures_dict.values()) / len(measures_dict))

def main():
    # program arguments
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--qrel', required=True, help='Path to qrel file')
    parser.add_argument('--results', required=True, help='Path to file containing results')
    parser.add_argument('--output_directory', required=True, help='Output directory path')

    cli = parser.parse_args()
    qrel = QrelsParser(cli.qrel).parse()
    output_directory = cli.output_directory

    # make output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    try:
        results = ResultsParser(cli.results).parse()
        name = results[0]
        # get measures
        measures = calculate_metrics(qrel, results)

        # write headers to csv file if it doesn't already exist
        if not os.path.exists(output_directory + "/average_measures.csv"):
            with open(output_directory + "/average_measures.csv", 'w', newline='') as csvfile:
                fieldNames = ['Run Name', 'Mean Average Precision', 'Mean P@10', 'Mean NDCG@10', 'Mean NDCG@1000']
                writer = csv.DictWriter(csvfile, fieldnames=fieldNames)
                writer.writeheader()

        write_measures_to_csv(name, output_directory, measures)
        write_average_measures_to_csv(name, output_directory, measures)
        print('measure, query_id, score')
        for key, measure in measures.items():
            for query, score in measure.items():
                print(key + ", " + query + ", " + str(f"{score:.3f}"))
        
    except(ResultsParser.ResultsParseError, QrelsParser.QrelsParseError, FileNotFoundError, ValueError):
        print("Bad format, can't compute measures for results file")

if __name__ == '__main__':
    main()
