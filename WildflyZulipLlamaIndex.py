# export ZULIP_TOKEN
# export OPENAI_API_KEY
# pip install llama-index-readers-zulip
# pip install zulip
# pip install llama-index

from llama_index.readers.zulip import ZulipReader
from llama_index.core import SummaryIndex

# Initialize the ZulipReader with the bot's email and Zulip domain
reader = ZulipReader(
    # TODO create bot and use those. Change this value
    # end provide yours ZULIP_TOKEN
    zulip_email="mchoma@redhat.com",
    zulip_domain="wildfly.zulipchat.com",
)

# testing data https://wildfly.zulipchat.com/#narrow/stream/194727-cloud/topic/Configuring.20WF.20in.20OpenShift
request="if i run oc apply -f charts/opentelemetry-collector.yaml, then helm install micrometer -f charts/helm.yaml wildfly/wildfly --wait --timeout=10m0s, it seems both... services (?) are installed and routes created. I can hit the REST endpoint from the Micrometer QS app, and the prometheus endpoint from the collector, but i get no metrics. if I view the logs from the micrometer pod, I get a bunch of connection refused errors, showing that WildFly is configured improperly. it is probably trying to push to localhost:4318, but should be the IP (or hostname) of the opentelemetrycollector pod. I do not know how, though, in this context, to get the IP, then configure WF..."

# Load data from specific streams - for PoC purposes just low traffic one
stream_names = ["cloud"]
data = reader.load_data(stream_names)
index = SummaryIndex.from_documents(data)
query_engine = index.as_query_engine()
response = query_engine.query(request)
print("Response with context:")
print(response)

index2 = SummaryIndex.from_documents([])
query_engine2 = index2.as_query_engine()
response2 = query_engine.query(request)
print("Response without context:")
print(response2)
