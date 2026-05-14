import asyncio
from sqlalchemy import select
from core.encryption import encryption_service, make_hash
from database.database import async_session_maker
from database.models import User

def is_encrypted(value: str | None) -> bool:
    if not value:
        return False

    return value.startswith("gAAAAA")

async def main():
    async with async_session_maker() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        updated = 0

        for user in users:
            changed = False

            if user.first_name and not is_encrypted(user.first_name):
                user.first_name = encryption_service.encrypt(user.first_name)
                changed = True

            if user.last_name and not is_encrypted(user.last_name):
                user.last_name = encryption_service.encrypt(user.last_name)
                changed = True

            if user.patronymic and not is_encrypted(user.patronymic):
                user.patronymic = encryption_service.encrypt(user.patronymic)
                changed = True

            if user.username and not is_encrypted(user.username):
                user.username = encryption_service.encrypt(user.username)
                changed = True

            if user.phone_number and not is_encrypted(user.phone_number):
                original_phone = user.phone_number

                user.phone_number = encryption_service.encrypt(original_phone)
                user.phone_hash = make_hash(original_phone)

                changed = True

            if changed:
                updated += 1
                print(f"Updated user {user.id}")

        await session.commit()

        print(f"\nDone. Updated users: {updated}")


if __name__ == "__main__":
    asyncio.run(main())