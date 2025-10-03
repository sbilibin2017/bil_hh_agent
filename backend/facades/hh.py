# from typing import NamedTuple
#
# import httpx
#
#
# class HHAuthTokenResponse(NamedTuple):
#     access_token: str
#     token_type: str
#     expires_in: int
#     refresh_token: str
#     scope: str
#
#
# class HHVacancyResponse(NamedTuple):
#     vacancy_id: str
#     title: str
#     url: str
#     employer: str
#
#
# class HHFacade:
#     def __init__(
#         self, client: httpx.AsyncClient, client_id: str, client_secret: str
#     ):
#         """
#         Фасад для работы с API HeadHunter.
#
#         :param client: Асинхронный HTTP-клиент (httpx.AsyncClient) с базовым URL
#         :param client_id: Идентификатор клиента для OAuth авторизации
#         :param client_secret: Секретный ключ клиента для OAuth авторизации
#         """
#         self.client = client
#         self.client_id = client_id
#         self.client_secret = client_secret
#
#     async def authorize(
#         self, username: str, password: str
#     ) -> HHAuthTokenResponse:
#         """
#         Авторизация пользователя на HH и получение токенов доступа.
#
#         :param username: Логин пользователя (email)
#         :param password: Пароль пользователя
#         :return: NamedTuple с access_token, refresh_token и информацией о сроке действия токена
#         """
#         data = {
#             "grant_type": "password",
#             "username": username,
#             "password": password,
#             "client_id": self.client_id,
#             "client_secret": self.client_secret,
#         }
#         headers = {"Content-Type": "application/x-www-form-urlencoded"}
#
#         response = await self.client.post(
#             "/oauth/token", data=data, headers=headers
#         )
#         response.raise_for_status()
#         token_data = response.json()
#
#         return HHAuthTokenResponse(
#             access_token=token_data["access_token"],
#             token_type=token_data.get("token_type", "bearer"),
#             expires_in=token_data.get("expires_in", 0),
#             refresh_token=token_data.get("refresh_token", ""),
#             scope=token_data.get("scope", ""),
#         )
#
#     async def list_ranked_vacancies(
#         self, access_token: str, limit: int = 20, page: int = 0
#     ) -> list[HHVacancyResponse]:
#         """
#         Получение списка вакансий, которые HH рекомендует текущему пользователю.
#         HeadHunter возвращает вакансии уже отсортированные по релевантности.
#
#         :param access_token: OAuth токен доступа пользователя
#         :param limit: Количество вакансий на страницу (по умолчанию 20)
#         :param page: Номер страницы (по умолчанию 0)
#         :return: Список NamedTuple с информацией о вакансии (id, название, url, работодатель)
#         """
#         headers = {"Authorization": f"Bearer {access_token}"}
#         params = {
#             "per_page": limit,
#             "page": page,
#             "order_by": "relevance",
#         }
#
#         response = await self.client.get(
#             "/vacancies", headers=headers, params=params
#         )
#         response.raise_for_status()
#         data = response.json()
#
#         return [
#             HHVacancyResponse(
#                 vacancy_id=item["id"],
#                 title=item["name"],
#                 url=item["url"],
#                 employer=item.get("employer", {}).get("name", ""),
#             )
#             for item in data.get("items", [])
#         ]
