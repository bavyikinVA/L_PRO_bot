import asyncio

from sqlalchemy import text
from database.database import async_session_maker
from database.models import Service, Specialist, SpecialistService


SPECIALISTS = [
    (1, "Анна", "Морозова", "5 лет", "app/static/images/master_morozova.jpg"),
    (2, "Андрей", "Кузнецов", "6 лет", "app/static/images/master_kuznetsov.jpg"),
    (3, "Мария", "Попова", "4 года", "app/static/images/master_popova.jpg"),
    (4, "Ольга", "Бондаренко", "7 лет", "app/static/images/master_bondarenko.jpg"),
    (5, "Дарья", "Иванова", "5 лет", "app/static/images/master_ivanova.jpg"),
    (6, "Ирина", "Игнатова", "8 лет", "app/static/images/master_ignatova.jpg"),
]

SERVICES = [
    (1, "RF-лифтинг", "Безоперационная подтяжка кожи с помощью радиоволн. Стимулирует выработку коллагена, улучшает упругость и сокращает морщины. Кожа становится более плотной и подтянутой уже после первой процедуры.", 2500, 60, None),
    (2, "Миостимуляция", "Процедура, которая с помощью электрических импульсов тренирует мышцы лица и тела. Улучшает тонус, подтягивает контуры и помогает избавиться от дряблости. Отличная альтернатива тренировкам.", 1800, 40, None),
    (3, "УЗ-чистка лица", "Глубокое очищение кожи с помощью ультразвука. Удаляет загрязнения, сужает поры и выравнивает тон лица. Кожа становится свежей, гладкой и сияющей.", 2200, 60, None),
    (4, "Лазерная эпиляция", "Современный способ удаления нежелательных волос. Обеспечивает длительный результат, делает кожу гладкой и избавляет от раздражений после бритья.", 3000, 30, None),
    (5, "Кавитация", "Аппаратная процедура для уменьшения жировых отложений. Разрушает жировые клетки и помогает скорректировать фигуру без боли и хирургии.", 2700, 50, None),
    (6, "LPG-массаж", "Вакуумно-роликовый массаж для борьбы с целлюлитом и улучшения контуров тела. Усиливает кровообращение и ускоряет обмен веществ.", 2000, 45, None),
    (7, "Микротоки", "Деликатная процедура омоложения с помощью слабых токов. Уменьшает отеки, подтягивает кожу и улучшает цвет лица.", 2100, 45, None),
    (8, "Дарсонваль", "Воздействие высокочастотными токами для улучшения состояния кожи. Помогает при акне, снижает жирность и ускоряет заживление.", 1200, 20, None),
    (9, "Фотоомоложение", "Световая терапия для омоложения кожи. Устраняет пигментацию, сосудистые звездочки и улучшает общий тон лица.", 3200, 50, None),
    (10, "Прессотерапия", "Лимфодренажный массаж с помощью давления воздуха. Снимает отеки, улучшает циркуляцию и помогает в борьбе с лишним весом.", 1700, 40, None),
    (11, "SMAS-лифтинг", "Глубокая подтяжка кожи с помощью ультразвука. Воздействует на мышечно-апоневротический слой, обеспечивая выраженный лифтинг-эффект.", 8000, 90, None),
    (12, "Карбокситерапия", "Процура насыщения кожи углекислым газом. Улучшает микроциркуляцию, выравнивает тон и придает коже свежий вид.", 2300, 40, None),
]

SPECIALIST_SERVICES = [
    (2, 1), (6, 1), (7, 1),
    (3, 2), (7, 2),
    (2, 3), (4, 3), (5, 3),
    (5, 4), (6, 4),
    (3, 5), (7, 5),
    (3, 6), (7, 6),
    (2, 7), (4, 7), (6, 7),
    (2, 8), (4, 8),
    (2, 9), (5, 9), (6, 9),
    (3, 10), (7, 10),
    (5, 11), (6, 11),
    (2, 12), (4, 12), (6, 12),
]


async def main():
    async with async_session_maker() as session:
        await session.execute(text(
            "TRUNCATE specialist_services, bookings, schedules, services, specialists "
            "RESTART IDENTITY CASCADE"
        ))

        for item in SPECIALISTS:
            session.add(Specialist(
                id=item[0],
                first_name=item[1],
                last_name=item[2],
                work_experience=item[3],
                photo=item[4],
            ))

        for item in SERVICES:
            session.add(Service(
                id=item[0],
                label=item[1],
                description=item[2],
                price=item[3],
                duration_minutes=item[4],
                icon=item[5],
            ))

        await session.flush()

        for specialist_id, service_id in SPECIALIST_SERVICES:
            session.add(SpecialistService(
                specialist_id=specialist_id,
                service_id=service_id,
            ))

        await session.execute(text("SELECT setval('specialists_id_seq', 7, true)"))
        await session.execute(text("SELECT setval('services_id_seq', 14, true)"))

        await session.commit()

    print("Seed completed successfully")


if __name__ == "__main__":
    asyncio.run(main())