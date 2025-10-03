import httpx


class ChatGPTFacade:
    def __init__(self, client: httpx.AsyncClient, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        Фасад для работы с ChatGPT для генерации сопроводительных писем.
        Клиент уже должен быть настроен с base_url и headers.

        :param client: Асинхронный HTTP-клиент (httpx.AsyncClient) с base_url и headers
        :param model: Бесплатная модель OpenAI (по умолчанию gpt-3.5-turbo)
        :param temperature: Температура генерации (по умолчанию 0.7)
        """
        self.client = client
        self.model = model
        self.temperature = temperature

    async def generate_cover_letter(self, user_profile: str, vacancy_title: str, vacancy_description: str) -> str:
        """
        Генерация сопроводительного письма с помощью бесплатной модели ChatGPT.

        :param user_profile: Опыт и профиль пользователя
        :param vacancy_title: Название вакансии
        :param vacancy_description: Описание вакансии
        :return: Сгенерированное сопроводительное письмо
        """
        prompt = (
            f"Напиши сопроводительное письмо для пользователя с опытом:\n{user_profile}\n"
            f"для вакансии '{vacancy_title}' с описанием:\n{vacancy_description}"
        )

        json_data: dict = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
        }

        response: httpx.Response = await self.client.post("/chat/completions", json=json_data)
        response.raise_for_status()
        data: dict = response.json()

        return data["choices"][0]["message"]["content"].strip()
