import requests
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue
import time

class OpenAI_API(QThread):
    response_received = pyqtSignal(dict, str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.prompt_queue = Queue()
        self.api_key = self.config["OpenAI"]["OPENAI_API_KEY"]
        self.llm_model = self.config["OpenAI"]["LLM_MODEL"]
        self.proxy = self.config["OpenAI"]["PROXY"]
        self.proxies = {
            "http": self.proxy,
            "https": self.proxy,
        }
        self.timeout_seconds = int(self.config["OpenAI"]["TIMEOUT_SECONDS"])
        self.max_retry = int(self.config["OpenAI"]["MAX_RETRY"])
        self.openaiapi_url = self.config["OpenAI"]["OPENAIAPI_URL"]
        self.top_p = float(self.config["OpenAI"]["TOP_P"])
        self.temperature = float(self.config["OpenAI"]["TEMPERATURE"])
        self.max_tokens = int(self.config["OpenAI"]["MAX_TOKENS"])
        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        self._configure_retry_strategy()

    def _configure_retry_strategy(self):
        retry_strategy = Retry(
            total=self.max_retry,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["GET", "POST"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def run(self):
        while True:
            prompt, context = self.prompt_queue.get()  # 从队列中获取 prompt 和 context
            self._generate_response(prompt, context)
            time.sleep(0.1)

    def _generate_response(self, prompt, context):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # 添加带有上下文的消息结构
        messages = [{"role": "system", "content": "You are an AI language model."}]

        # 在发送的消息中包含上下文
        if context:
            for msg in context.split('\n'):
                if not msg or ': ' not in msg:
                    continue
                role, content = msg.split(': ', 1)
                messages.append({"role": role.lower(), "content": content.strip()})

        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.llm_model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }

        try:
            time.sleep(2)
            response = self.session.post(
                self.openaiapi_url, headers=headers, json=data, proxies=self.proxies, timeout=self.timeout_seconds
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            print(f"Error details: {e.response.text}")
            result = {"error": str(e)}
        self.response_received.emit(result, prompt)

