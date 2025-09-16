import os
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel

google_api_key = os.getenv("GOOGLE_API_KEY")

_= load_dotenv()

model = LiteLLMModel(model_id="gemini/gemini-2.5-pro", api_key=google_api_key, temperature=0.0)

agent = CodeAgent(tools=[], model=model)

agent.run("1,1,2,3,5,8,...と続き10項めが55となる数列の128項めを求めてください。")