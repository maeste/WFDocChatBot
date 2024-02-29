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

def read_documents() :        
    # Create a docs directory to store the downloaded PDF files
    if not os.path.exists(docs_dir):
        os.mkdir(docs_dir)

    # PDFs to be ingested    
    docs_url_prefix = "https://access.redhat.com/documentation/en-us/red_hat_jboss_enterprise_application_platform/8.0/pdf/"
    docs = ["introduction_to_red_hat_jboss_enterprise_application_platform/red_hat_jboss_enterprise_application_platform-8.0-introduction_to_red_hat_jboss_enterprise_application_platform-en-us.pdf",
            "configuring_ssltls_in_jboss_eap/red_hat_jboss_enterprise_application_platform-8.0-configuring_ssltls_in_jboss_eap-en-us.pdf",
            "getting_started_with_red_hat_jboss_enterprise_application_platform/red_hat_jboss_enterprise_application_platform-8.0-getting_started_with_red_hat_jboss_enterprise_application_platform-en-us.pdf",
            "getting_started_with_management_console/red_hat_jboss_enterprise_application_platform-8.0-getting_started_with_management_console-en-us.pdf",
            "using_jboss_eap_on_openshift_container_platform/red_hat_jboss_enterprise_application_platform-8.0-using_jboss_eap_on_openshift_container_platform-en-us.pdf",
            "red_hat_jboss_enterprise_application_platform_installation_methods/red_hat_jboss_enterprise_application_platform-8.0-red_hat_jboss_enterprise_application_platform_installation_methods-en-us.pdf",
            "updating_red_hat_jboss_enterprise_application_platform/red_hat_jboss_enterprise_application_platform-8.0-updating_red_hat_jboss_enterprise_application_platform-en-us.pdf",
            "performance_tuning_for_red_hat_jboss_enterprise_application_platform/red_hat_jboss_enterprise_application_platform-8.0-performance_tuning_for_red_hat_jboss_enterprise_application_platform-en-us.pdf", 
            "getting_started_with_developing_applications_for_jboss_eap_deployment/Red_Hat_JBoss_Enterprise_Application_Platform-8.0-Getting_started_with_developing_applications_for_JBoss_EAP_deployment-en-US.pdf",
            "migration_guide/red_hat_jboss_enterprise_application_platform-8.0-migration_guide-en-us.pdf",
            "using_the_jboss_server_migration_tool/red_hat_jboss_enterprise_application_platform-8.0-using_the_jboss_server_migration_tool-en-us.pdf",
            "secure_storage_of_credentials_in_jboss_eap/red_hat_jboss_enterprise_application_platform-8.0-secure_storage_of_credentials_in_jboss_eap-en-us.pdf",
            "securing_applications_and_management_interfaces_using_an_identity_store/red_hat_jboss_enterprise_application_platform-8.0-securing_applications_and_management_interfaces_using_an_identity_store-en-us.pdf",
            "securing_applications_and_management_interfaces_using_multiple_identity_stores/red_hat_jboss_enterprise_application_platform-8.0-securing_applications_and_management_interfaces_using_multiple_identity_stores-en-us.pdf",
            "using_single_sign-on_with_jboss_eap/red_hat_jboss_enterprise_application_platform-8.0-using_single_sign-on_with_jboss_eap-en-us.pdf"  
        ]

    # TODO, make use of this config guide too if needed
    docs_config_guide = "https://access.redhat.com/documentation/en-us/red_hat_jboss_enterprise_application_platform/7.4/pdf/configuration_guide/red_hat_jboss_enterprise_application_platform-7.4-configuration_guide-en-us.pdf"

    # Download the PDFs if the docs directory is currently empty
    if not os.listdir(docs_dir): 
        for doc in docs:
            response = requests.get(docs_url_prefix + doc, stream=True)
            pdf_file_name = os.path.basename(doc)   
            if response.status_code == 200:
                filepath = os.path.join(docs_dir, pdf_file_name)
                with open(filepath, 'wb') as pdf_object:
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
    if not os.path.isdir(docs_dir):
        read_documents()
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
        response = chat_engine.chat("How do I configure TLSv1.3 with elytron?")
        for source_node in response.source_nodes:
            source_details = "File: " + source_node.metadata['file_name'] + ", Page: " + source_node.metadata['page_label']
    
        print(response)
        print(source_details)

    print("Done")

main()
    
    
