import sys
import os
import json

def main():
    document_file_path = ""
    metadata_file_path = ""

    if len(sys.argv) != 4:
        print("Wrong number of inputs, please enter GetDoc followed by a path to the location of the documents and metadata store, the string 'id' or 'docno' and the internal integer id or the DOCNO!")
        print("For example, from the command prompt, this would look like the following if in the correct folder where the programs are stored:")
        print("python GetDoc.py /searchengines/mini-collection-index id 0\nor")
        print("python GetDoc.py /searchengines/mini-collection-index docno LA010189-0001")
        sys.exit()
    
    file_path = sys.argv[1]
    string_reference = sys.argv[2]
    doc_no_or_id_classifier = sys.argv[3]

    if string_reference == "docno":
        yy = doc_no_or_id_classifier[6:8]
        mm = doc_no_or_id_classifier[2:4]
        dd = doc_no_or_id_classifier[4:6]
        
        document_file_path = file_path + f"/{yy}/{mm}/{dd}/{doc_no_or_id_classifier}.txt"
        metadata_file_path = file_path + f"/{yy}/{mm}/{dd}/{doc_no_or_id_classifier}.json"
    elif string_reference == "id":
        docnos_document_path = file_path + "/docnos.txt"
        if os.path.exists(docnos_document_path):
            with open(docnos_document_path, 'r') as docnos_file:
                docnos = [docno.strip() for docno in docnos_file]
            try: 
                docno = docnos[int(doc_no_or_id_classifier)]
                yy = docno[6:8]
                mm = docno[2:4]
                dd = docno[4:6]

                document_file_path = file_path + f"/{yy}/{mm}/{dd}/{docno}.txt"
                metadata_file_path = file_path + f"/{yy}/{mm}/{dd}/{docno}.json"
            except IndexError:
                print("The internal id integer provided does not exist. Try entering a new id!")
                sys.exit()

            
        else:
            print("Unable to find docnos.txt and can't map internal integer id to docno!")
            sys.exit()

    if os.path.exists(document_file_path):
        with open(document_file_path, 'r') as document_file:
            document = document_file.read() 
    else:
        print("Unable to find document file, this document number does not exist. Try entering a new docno!")
        sys.exit()

    if os.path.exists(metadata_file_path): 
        with open(metadata_file_path, 'r') as metadata_file:
            metadata = json.load(metadata_file)
    else:
        print("Unable to find metadata file. Try entering a new docno!")
        sys.exit()
        
    doc_no = metadata['docno']
    internal_id = metadata['internal id']
    date = metadata['date']
    headline = metadata['headline']

    print(f"docno: {doc_no}\ninternal id: {internal_id}\ndate: {date}\nheadline: {headline}\nraw document:\n{document}")

if __name__=="__main__":
    main()