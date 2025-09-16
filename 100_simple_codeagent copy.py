import os
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel, REMOVE_PARAMETER

_= load_dotenv()
oci_user = os.getenv("OCI_USER")
oci_fingerprint = os.getenv("OCI_FINGERPRINT")
oci_tenancy = os.getenv("OCI_TENANCY")
oci_region = os.getenv("OCI_REGION")
oci_key = os.getenv("OCI_KEY")
oci_compartment_id = os.getenv("OCI_COMPARTMENT_ID")

model = LiteLLMModel(
    model_id="oci/xai.grok-4",
    oci_region=os.getenv("OCI_REGION"),                    # 例: "us-chicago-1"
    oci_user=os.getenv("OCI_USER"),                        # OCI User OCID
    oci_fingerprint=os.getenv("OCI_FINGERPRINT"),          # RSA key fingerprint
    oci_tenancy=os.getenv("OCI_TENANCY"),                  # Tenancy OCID
    oci_key=os.getenv("OCI_KEY"),                          # Private key content
    oci_compartment_id=os.getenv("OCI_COMPARTMENT_ID"),    # Compartment OCID
    stop=REMOVE_PARAMETER, 
    temperature=0.0,
    max_tokens= 10000,
    drop_params=True
)

agent = CodeAgent(tools=[], model=model)

agent.run("1,1,2,3,5,8,...と続き10項めが55となる数列の128項めを求めてください。")