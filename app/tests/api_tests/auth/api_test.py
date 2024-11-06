from httpx import AsyncClient


async def test_register_user(ac: AsyncClient):
    response = await ac.post("api/v1/auth/register", json={
        "email": "example@example.com",
        "username": "example_username",
        "password": "example_password",
        "password_repiet": "example_password"
    })
    assert response.status_code == 201