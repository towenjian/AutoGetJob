from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
import logging

log = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

class AiAsk:
    def __init__(self, api_key, model:str|list[str],base_url):
        self.client = OpenAI(api_key=api_key,base_url=base_url)
        self.model = model
        if isinstance(model, list):
            self.index = 0

    def test_client(self):
        def test_func(model_):
            try:
                response = self.client.chat.completions.create(
                    model=model_,
                    messages=[
                        ChatCompletionSystemMessageParam(role="system", content="你是一个智能助手"),
                        ChatCompletionUserMessageParam(role="user", content="你是什么模型？"),
                    ],
                    temperature=0.9,
                    max_tokens=1000,
                )
                logging.info(response.choices[0].message.content)
                return True
            except Exception as e:
                logging.error(e)
                return False
        if isinstance(self.model, list):
            f = []
            for index ,model in enumerate(self.model):
                log.info(f"正在测试第{index}个模型: {model}")
                if test_func(model):
                    f.append(True)
            return all(f)
        else:
            return test_func(self.model)

    def ask(self, prompt: str, system_prompt: str, max_tokens=1000, timeout=30):

        def get_answer(model_):
            response = self.client.chat.completions.create(
                model=model_,
                messages=[
                    ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                    ChatCompletionUserMessageParam(role="user", content=prompt),
                ],
                temperature=0.9,
                max_tokens=max_tokens,
                timeout=timeout
            )
            return response.choices[0].message.content

        if isinstance(self.model, list):
            try:
                return get_answer(self.model[self.index])
            except Exception as e:
                log.warning(f"当前模型产生错误，以切换到下一个模型进行测试\n错误信息为: {e}")
                self.index += 1
                if self.index >= len(self.model):
                    log.warning("所有模型均产生错误，请检查模型是否正确")
                    exit(1)
                return get_answer(self.model[self.index])
        else:
            try:
                return get_answer(self.model)
            except Exception as e:
                log.warning(f"当前模型产生错误，请检查模型是否正确\n错误信息为: {e}")
                exit(1)
