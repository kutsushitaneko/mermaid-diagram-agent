import os
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel

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
    temperature=0.0,
    max_tokens= 10000,
    drop_params=True
)

agent = CodeAgent(tools=[],
    model=model,
    additional_authorized_imports=['requests', 'bs4']
)

agent.run("以下のREST APIでqパラメータに指定した地名、もしくは住所の緯度・経度を取得できます。緯度経度取得REST API URL: https://msearch.gsi.go.jp/address-search/AddressSearch?q=地名または住所。複数の候補地の情報が返されるので注意してください。先頭が正しいとは限りません。また、次のREST API で緯度経度から天気予報を取得できます。天気予報取得REST API URL: https://api.open-meteo.com/v1/forecast?latitude=緯度&longitude=経度&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset&hourly=temperature_2m,relative_humidity_2m,weather_code&timezone=Asia%2FTokyo&forecast_days=2 。東京ディズニーランドの明日の天気はレジャー日和ですか？その理由は？")