import sys
import gzip
import os
import io
import re
from datetime import datetime
import json
from PorterStemmer import PorterStemmer

DOC_OPENING_TAG = "<DOC>"
DOC_NO_TAG = "<DOCNO>"
HEADLINE_OPENING_TAG = "<HEADLINE>"
HEADLINE_CLOSING_TAG = "</HEADLINE>"
P_OPENING_TAG = "<P>"
P_CLOSING_TAG = "</P>"
DOC_CLOSING_TAG = "</DOC>"

def save_document_and_metadata(storage_path, mmddyy, doc_no, document_metadata, raw_document):
    file_path = create_directory(storage_path, mmddyy)
    document_file_path = file_path + f"/{doc_no}.txt"
    metadata_file_path = file_path + f"/{doc_no}.json"

    with open(document_file_path, 'w') as document_file:
        document_file.write(raw_document)

    with open(metadata_file_path, 'w') as metadata_file:
        json.dump(document_metadata, metadata_file, indent=4)

def create_directory(storage_path, mmddyy):
    month = mmddyy[:2]
    day = mmddyy[2:4]
    year = mmddyy[4:]

    mmddyy_directory = f"/{year}/{month}/{day}"

    file_path = storage_path + mmddyy_directory

    if not os.path.exists(file_path):
        os.makedirs(file_path)
    
    return file_path

def format_date(doc_no):
    doc_no_split = doc_no.split('-')
    mmddyy = doc_no_split[0][2:]
    date = datetime.strptime(mmddyy, '%m%d%y')
    date = date.replace(year = 1900 + date.year % 100)
    formatted_date = date.strftime('%B %d, %Y')

    return mmddyy, formatted_date

def write_to_docnos(doc_no, storage_path):
    docnos_file_path = storage_path + "/docnos.txt"

    with open(docnos_file_path, 'a') as docnos_file:
        docnos_file.write(doc_no + "\n")

def create_metadata_dictionary(doc_no, internal_id, date, headline):
    return {
        'docno': doc_no,
		'internal id': internal_id,
        'date': date,
        'headline': headline
    }

def tokenize(text, tokens, stem):
    text = text.lower() 
    porterStemmer = PorterStemmer()
    start = 0 
    i = 0

    for currChar in text:
        if not currChar.isdigit() and not currChar.isalpha() :
            if start != i :
                token = text[start:i]
                if stem:
                    token = porterStemmer.stem(token, 0, len(token) - 1)
                tokens.append(token)
                
            start = i + 1

        i = i + 1

    if start != i :
        token = text[start:i]
        if stem:
            token = porterStemmer.stem(token, 0, len(token) - 1)
        tokens.append(token)

def tokenize_strings(strings, tokens, stem):
    for string in strings:
        tokenize(string, tokens, stem)

def tokenize_relevant_text(raw_document, stem):
    tokens = []
    relevant_text_strings = []

    text_headline_graphic_regex = re.compile(
        r'<TEXT>([\s\S]+?)<\/TEXT>|<HEADLINE>([\s\S]+?)<\/HEADLINE>|<GRAPHIC>([\s\S]+?)<\/GRAPHIC>'
    )

    matches = text_headline_graphic_regex.findall(raw_document)

    for match in matches:
        for group in match:
            if group:
                relevant_text = strip_all_tags(group.strip())
                relevant_text_strings.append(relevant_text)

    tokenize_strings(relevant_text_strings, tokens, stem)

    return tokens

def strip_all_tags(text):
    strip_tags_regex = re.compile(r'<[^>]+>')
    stripped_text = strip_tags_regex.sub('', text)
    return stripped_text

def write_to_doclengths(doc_length, storage_path):
    doclengths_file_path = storage_path + "/doc-lengths.txt"

    with open(doclengths_file_path, 'a') as doclengths_file:
        doclengths_file.write(str(doc_length) + "\n")

def convert_tokens_to_ids(tokens, lexicon):
    token_ids = []
    for token in tokens:
        if token in lexicon:
            token_ids.append(lexicon[token])
        else:
            id = len(lexicon)
            lexicon[token] = id
            token_ids.append(id)
    
    return token_ids

def count_words(token_ids):
    word_counts = {}
    for id in token_ids:
        if id in word_counts:
            word_counts[id] += 1
        else:
            word_counts[id] = 1
    
    return word_counts

def add_to_postings(word_counts, doc_id, inv_index):
    for term_id in word_counts:
        count = word_counts[term_id]
        postings = []
        if term_id in inv_index:
            postings = inv_index[term_id]
        postings.append(doc_id)
        postings.append(count)
        inv_index[term_id] = postings

def write_lexicon(lexicon, storage_path):
    lexicon_file_path = storage_path + "/lexicon.json"

    with open(lexicon_file_path, 'w') as lexicon_file:
        json.dump(lexicon, lexicon_file, indent=4)

def write_inverted_index(inverted_index, storage_path):
    inverted_index_file_path = storage_path + "/inverted-index.json"

    with open(inverted_index_file_path, 'w') as inverted_index_file:
        json.dump(inverted_index, inverted_index_file, indent=4)

def main():
    
    # initialize variables
    doc_no_array = []
    internal_id = 0
    is_headline = False
    headline = ""
    mmddyy = ""
    formatted_date = ""
    doc_no = ""
    lexicon = {}
    inverted_index = {}

    if len(sys.argv) != 4:
        print("Wrong number of inputs, please enter IndexEngine followed by a file path to the latimes.gz file, a file path to the storage folder, and a boolean true or false if stemming is wanted.")
        print("For example, from the command prompt, this would look like the following if in the correct folder: python IndexEngine.py /searchengines/MiniCollection.gz /searchengines/mini-collection-index true")
        sys.exit()
    
    gzip_path = sys.argv[1]
    storage_path = sys.argv[2]
    stem = sys.argv[3]

    if not os.path.exists(gzip_path):
        print("This data path does not exist! Please enter a valid path to the latimes file!")
        sys.exit()
    if os.path.exists(storage_path):
        print("This storage directory already exists! Either change the storage path to one that doesn't exist or delete the existing directory for the path you listed and rerun the program!")
        sys.exit()
    else:
        os.makedirs(storage_path)
        print(f"The directory {storage_path} has been created")

    stem = stem.lower() == "true"

    with gzip.open(gzip_path, 'rt') as gzip_file:
        string_buffer = io.StringIO()

        for line in gzip_file:
            string_buffer.write(line)

            if HEADLINE_OPENING_TAG in line:
                is_headline = True
            if is_headline == True and P_OPENING_TAG not in line and P_CLOSING_TAG not in line:
                headline += line.strip() + " "
            if HEADLINE_CLOSING_TAG in line:
                is_headline = False

            if DOC_NO_TAG in line:
                doc_no = re.search(r'LA\d{6}-\d{4}', line).group()
                doc_no_array.append(doc_no)
                mmddyy, formatted_date = format_date(doc_no)

            if DOC_CLOSING_TAG in line:
                raw_document = string_buffer.getvalue()

                # strip headline of headline tags
                headline = re.sub(r'<\/?HEADLINE>', '', headline).strip()

                # create metadata dictionary
                document_metadata = create_metadata_dictionary(doc_no, internal_id, formatted_date, headline)
                
                # save document
                save_document_and_metadata(storage_path, mmddyy, doc_no, document_metadata, raw_document)

                # break text, headline and graphic text into tokens
                tokens = tokenize_relevant_text(raw_document, stem)

                # get doc_length and write to doc_lengths file
                doc_length = len(tokens)
                write_to_doclengths(doc_length, storage_path)

                # write to internal docnos
                write_to_docnos(doc_no, storage_path)

                # get word counts of the terms and append to the postings
                token_ids = convert_tokens_to_ids(tokens, lexicon)
                word_counts = count_words(token_ids)
                add_to_postings(word_counts, internal_id, inverted_index)

                string_buffer.seek(0)
                string_buffer.truncate()
                headline = ""
                internal_id += 1

        # write to lexicon file and inverted index file
        write_lexicon(lexicon, storage_path)
        write_inverted_index(inverted_index, storage_path)
        string_buffer.close()
    
if __name__=="__main__":
    main()