from app.db import get_connection


class TelegramRepository:
    def upsert_authorized_user(self, chat_id: str, username: str | None, role: str = "operator") -> None:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO authorized_telegram_users (chat_id, username, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (chat_id) DO UPDATE SET username=excluded.username, role=excluded.role
                """,
                (chat_id, username, role),
            )
        connection.commit()
        connection.close()

    def get_role(self, chat_id: str) -> str | None:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT role FROM authorized_telegram_users WHERE chat_id = %s", (chat_id,))
            row = cursor.fetchone()
        connection.close()
        return row["role"] if row else None

    def is_authorized(self, chat_id: str) -> bool:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM authorized_telegram_users WHERE chat_id = %s", (chat_id,))
            row = cursor.fetchone()
        connection.close()
        return bool(row)

    def delete_subscription(self, chat_id: str) -> None:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM summary_subscriptions WHERE chat_id = %s", (chat_id,))
        connection.commit()
        connection.close()

    def upsert_summary_subscription(self, chat_id: str) -> None:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO summary_subscriptions (chat_id)
                VALUES (%s)
                ON CONFLICT (chat_id) DO NOTHING
                """,
                (chat_id,),
            )
        connection.commit()
        connection.close()

    def list_summary_subscribers(self) -> list[dict]:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT chat_id FROM summary_subscriptions")
            rows = cursor.fetchall()
        connection.close()
        return rows

    def create_audit_log(
        self,
        chat_id: str,
        username: str | None,
        command: str,
        payload: str,
        status: str,
        error: str | None,
    ) -> None:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_log (chat_id, username, command, payload, status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (chat_id, username, command, payload, status, error),
            )
        connection.commit()
        connection.close()
