import argparse
import logging
import sys
import os
import requests
from llama_index.core import VectorStoreIndex
from llama_index.core import SimpleDirectoryReader
from llama_index.core import (
    VectorStoreIndex,
    load_index_from_storage,
    StorageContext,
    )
from llama_index.core import VectorStoreIndex
from llama_index.core.memory import ChatMemoryBuffer
    
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
docs_dir = os.path.join(os.getcwd(), "docs")
storage_dir = os.path.join(os.getcwd(), "storage")

def read_documents(docs_path) :        
    # Create a docs directory to store the downloaded PDF files
    if not os.path.exists(docs_dir):
        os.mkdir(docs_dir)

    # Download the PDFs if the docs directory is currently empty
    if not os.listdir(docs_dir):
        with open(docs_path, 'r') as file:
            for doc in file:
                doc = doc.rstrip('\n')
                response = requests.get(doc, stream=True)
                pdf_file_name = os.path.basename(doc)   
                if response.status_code == 200:
                    file_path = os.path.join(docs_dir, pdf_file_name)
                    with open(file_path, 'wb') as pdf_object:
                        pdf_object.write(response.content)
                        #print(pdf_file_name)

    
def createIndex():

    documents = SimpleDirectoryReader(docs_dir).load_data()

    #print(documents)
    v_index = VectorStoreIndex.from_documents(documents)
    v_index.set_index_id("vector_index")
    v_index.storage_context.persist(storage_dir)
    return v_index

def read_index() :
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir="storage")
    # load index
    return load_index_from_storage(storage_context, index_id="vector_index")

def init_chat_emgine(v_index) :
    memory = ChatMemoryBuffer.from_defaults(token_limit=1500)
    chat_engine = v_index.as_chat_engine(
        chat_mode="context",
        memory=memory,
        system_prompt=(
            "You are a chatbot that will provide assistance with questions about JBoss Enterprise Application Platform (also known as JBoss EAP)."
            + "You will be given a question you need to answer and a context to provide you with information."
            + "You must answer the question based as much as possible on this context."
            + "If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct."
            + "If you don't know the answer to a question, please don't share false information."
        ))
    return chat_engine


def main() :
    print("starting....")
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs_path", '-d', help="Path to a file containing URLs for PDF files to be downloaded and ingested.\
    Defaults to data/eap8_docs.txt", type=str, default ="data/eap8_docs.txt")
    args = parser.parse_args()
    if not os.path.isdir(docs_dir):
        read_documents(args.docs_path)
    if not os.path.isdir(storage_dir):
        v_index = createIndex()
    else :
        v_index = read_index()
    chat_engine = init_chat_emgine(v_index)
    print("Ready...\n")
    while True:
        data = input("Please enter the message:\n")
        if 'Exit' == data:
            break
        response = chat_engine.chat(data)
        for source_node in response.source_nodes:
            source_details = "File: " + source_node.metadata['file_name'] + ", Page: " + source_node.metadata['page_label']
    
        print(response)
        print(source_details)

    print("Done")

main()
    
    
