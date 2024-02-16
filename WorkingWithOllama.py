# pip install llama-index
# pip install llama-index-readers-web

from llama_index.core import KeywordTableIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.core import SummaryIndex
from llama_index.readers.web import SimpleWebPageReader

documents = SimpleDirectoryReader("data").load_data()
# define LLM
llm = Ollama(model="mistral:7b-instruct-v0.2-q2_K", request_timeout=30.0, base_url="http://ollama-mchomaredhatcom.apps.ai-hackathon.qic7.p1.openshiftapps.com:80")
# Or localhost
# llm = Ollama(model="mistral:7b-instruct-v0.2-q2_K", request_timeout=30.0)

documents = SimpleWebPageReader(html_to_text=True).load_data(
    ["https://docs.wildfly.org/31/Client_Guide.html"]
)

# build index
index = SummaryIndex.from_documents(documents, llm=llm)
query_engine = index.as_query_engine()
response = query_engine.query("How to configure authentication?")
print(response)
