import argparse
import logging
import sys
import os
import requests
from llama_index.agent.openai import OpenAIAssistantAgent
from llama_index.core import VectorStoreIndex
from llama_index.core import SimpleDirectoryReader
from llama_index.core import (
    VectorStoreIndex,
    load_index_from_storage,
    StorageContext,
    )
from llama_index.core import VectorStoreIndex
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import QueryEngineTool
from llama_index.readers.web import SimpleWebPageReader

VECTOR_INDEX = "vector_index"
DOCS_STORAGE = "docs_storage"
URLS_STORAGE = "urls_storage"

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
docs_dir = os.path.join(os.getcwd(), "docs")
docs_storage_dir = os.path.join(os.getcwd(), DOCS_STORAGE)
urls_storage_dir = os.path.join(os.getcwd(), URLS_STORAGE)

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


def read_urls(urls_path):
    file = open(urls_path, 'r')
    urls = file.read().splitlines()
    documents = SimpleWebPageReader(html_to_text=True).load_data(urls)
    #print(documents)
    file.close()
    return documents

        
def create_docs_index(docs_dir):
    docs = SimpleDirectoryReader(docs_dir).load_data()
    return create_index(docs, docs_storage_dir)


def create_urls_index(urls_path):
    urls = read_urls(urls_path)
    return create_index(urls, urls_storage_dir)

def create_index(documents, storage_dir):
    v_index = VectorStoreIndex.from_documents(documents)
    v_index.set_index_id(VECTOR_INDEX)
    v_index.storage_context.persist(storage_dir)
    return v_index

def read_index(storage) :
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=storage)
    # load index
    return load_index_from_storage(storage_context, index_id=VECTOR_INDEX)

def init_agent(docs_v_index, urls_v_index):
    docs_query_engine = docs_v_index.as_query_engine()
    urls_query_engine = urls_v_index.as_query_engine()
    
    docs_tool = QueryEngineTool.from_defaults(query_engine=docs_query_engine, name="docs_tool", description=("Useful for retrieving detailed information about JBoss Enterprise Application Platform, also known as JBoss EAP, along with example CLI commands."))

    urls_tool = QueryEngineTool.from_defaults(query_engine=urls_query_engine, name="urls_tool", description=("Useful for retrieving information about valid syntax for CLI commands for JBoss Enterprise Application Platform, also known as JBoss EAP."))
    
    # TODO: Determine if OpenAIAssistantAgents support memory configuration
    agent = OpenAIAssistantAgent.from_new(
        name="EAP Assistance Bot",
        instructions="You are a chatbot that will provide assistance with questions about JBoss Enterprise Application Platform (also known as JBoss EAP)."
            + "You will be given a question you need to answer and a context to provide you with information."
            + "You must answer the question based as much as possible on this context."
            + "If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct."
            + "If you don't know the answer to a question, please don't share false information."
            + "Your response must include CLI commands with valid syntax for JBoss Enterprise Application Platform, also known as JBoss EAP.",
        openai_tools=[],
        tools=[docs_tool, urls_tool],
        verbose=True,
        run_retrieve_sleep_time=1.0)
    return agent
    


def main() :
    print("starting....")
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs_path", '-d', help="Path to a file containing URLs for PDF files to be downloaded and ingested.\
    Defaults to data/eap8_docs.txt", type=str, default ="data/eap8_docs.txt")
    parser.add_argument("--urls_path", '-u', help="Path to a file containing URLs to be read.\
    Defaults to data/wildscribe_urls.txt", type=str, default ="data/wildscribe_urls.txt")
    args = parser.parse_args()
    
    if not os.path.isdir(docs_dir):
        read_documents(args.docs_path)

    # create docs index if needed
    if not os.path.isdir(docs_storage_dir):
        docs_v_index = create_docs_index(docs_dir)
    else:
        docs_v_index = read_index(DOCS_STORAGE)

    # create urls index if needed
    if not os.path.isdir(urls_storage_dir):
        urls_v_index = create_urls_index(args.urls_path)
    else:
        urls_v_index = read_index(URLS_STORAGE)    
    
    agent = init_agent(docs_v_index, urls_v_index)
    print("Ready...\n")
    while True:
        data = input("Please enter the message:\n")
        if 'Exit' == data:
            break
        response = agent.chat(data)
        for source_node in response.source_nodes:
            file = ""
            page = ""
            if 'file_name' in source_node.metadata:
                file = source_node.metadata['file_name']
            else:
                print(source_node)
            if 'page_label' in source_node.metadata:
                page = source_node.metadata['page_label']
            source_details = "File: " + file + ", Page: " + page
    
        print(response)
        print(source_details)

    print("Done")

main()
