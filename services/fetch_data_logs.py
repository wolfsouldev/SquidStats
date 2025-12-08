import logging
import re
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, inspect
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from database.database import get_concat_function, get_dynamic_models, get_session

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Patrones de validación para nombres de tabla y fechas
TABLE_NAME_PATTERN = re.compile(r"^[a-z_]{3,20}$")
DATE_SUFFIX_PATTERN = re.compile(r"^\d{8}$")


def validate_table_name(table_name: str) -> bool:
    return bool(TABLE_NAME_PATTERN.match(table_name))


def validate_date_suffix(date_suffix: str) -> bool:
    return bool(DATE_SUFFIX_PATTERN.match(date_suffix))


def sanitize_table_name(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", name.lower())


def get_dynamic_model(db: Session, table_name: str, date_suffix: str):
    # Validar parámetros
    if not validate_table_name(table_name):
        logger.error(f"Invalid table name: {table_name}")
        return None

    if not validate_date_suffix(date_suffix):
        logger.error(f"Invalid date suffix: {date_suffix}")
        return None

    full_table_name = f"{table_name}_{date_suffix}"

    # Check if the table exists
    try:
        inspector = inspect(db.get_bind())
        if not inspector.has_table(full_table_name):
            logger.warning(f"Table {full_table_name} not found")
            return None

        # Create dynamic model using automap
        Base = automap_base()
        Base.prepare(autoload_with=db.get_bind())

        return getattr(Base.classes, full_table_name, None)
    except Exception as e:
        logger.error(f"Error getting dynamic model: {str(e)}", exc_info=True)
        return None


def get_users_logs(
    db: Session,
    date_suffix: str | None = None,
    page: int = 1,
    per_page: int = 15,
    search: str | None = None,
) -> dict[str, Any]:
    # # Array de 20 usuarios de ejemplo
    # sample_users = [
    #     {
    #         "user_id": 1,
    #         "username": "jsmith",
    #         "ip": "192.168.1.10",
    #         "logs": [
    #             {
    #                 "url": "http://example.com",
    #                 "response": 200,
    #                 "request_count": 45,
    #                 "data_transmitted": 2048000,
    #             },
    #             {
    #                 "url": "http://google.com",
    #                 "response": 200,
    #                 "request_count": 32,
    #                 "data_transmitted": 1024000,
    #             },
    #         ],
    #         "total_requests": 77,
    #         "total_data": 3072000,
    #     },
    #     {
    #         "user_id": 2,
    #         "username": "ajones",
    #         "ip": "192.168.1.11",
    #         "logs": [
    #             {
    #                 "url": "http://github.com",
    #                 "response": 200,
    #                 "request_count": 23,
    #                 "data_transmitted": 512000,
    #             },
    #         ],
    #         "total_requests": 23,
    #         "total_data": 512000,
    #     },
    #     {
    #         "user_id": 3,
    #         "username": "mbrown",
    #         "ip": "192.168.1.12",
    #         "logs": [
    #             {
    #                 "url": "http://stackoverflow.com",
    #                 "response": 200,
    #                 "request_count": 89,
    #                 "data_transmitted": 4096000,
    #             },
    #         ],
    #         "total_requests": 89,
    #         "total_data": 4096000,
    #     },
    #     {
    #         "user_id": 4,
    #         "username": "rgarcia",
    #         "ip": "192.168.1.13",
    #         "logs": [
    #             {
    #                 "url": "http://youtube.com",
    #                 "response": 200,
    #                 "request_count": 156,
    #                 "data_transmitted": 10240000,
    #             },
    #         ],
    #         "total_requests": 156,
    #         "total_data": 10240000,
    #     },
    #     {
    #         "user_id": 5,
    #         "username": "pmiller",
    #         "ip": "192.168.1.14",
    #         "logs": [
    #             {
    #                 "url": "http://linkedin.com",
    #                 "response": 200,
    #                 "request_count": 34,
    #                 "data_transmitted": 1536000,
    #             },
    #         ],
    #         "total_requests": 34,
    #         "total_data": 1536000,
    #     },
    #     {
    #         "user_id": 6,
    #         "username": "ldavis",
    #         "ip": "192.168.1.15",
    #         "logs": [
    #             {
    #                 "url": "http://twitter.com",
    #                 "response": 200,
    #                 "request_count": 67,
    #                 "data_transmitted": 2560000,
    #             },
    #         ],
    #         "total_requests": 67,
    #         "total_data": 2560000,
    #     },
    #     {
    #         "user_id": 7,
    #         "username": "crodriguez",
    #         "ip": "192.168.1.16",
    #         "logs": [
    #             {
    #                 "url": "http://facebook.com",
    #                 "response": 200,
    #                 "request_count": 45,
    #                 "data_transmitted": 3072000,
    #             },
    #         ],
    #         "total_requests": 45,
    #         "total_data": 3072000,
    #     },
    #     {
    #         "user_id": 8,
    #         "username": "mwilson",
    #         "ip": "192.168.1.17",
    #         "logs": [
    #             {
    #                 "url": "http://wikipedia.org",
    #                 "response": 200,
    #                 "request_count": 23,
    #                 "data_transmitted": 1024000,
    #             },
    #         ],
    #         "total_requests": 23,
    #         "total_data": 1024000,
    #     },
    #     {
    #         "user_id": 9,
    #         "username": "jlee",
    #         "ip": "192.168.1.18",
    #         "logs": [
    #             {
    #                 "url": "http://amazon.com",
    #                 "response": 200,
    #                 "request_count": 78,
    #                 "data_transmitted": 5120000,
    #             },
    #         ],
    #         "total_requests": 78,
    #         "total_data": 5120000,
    #     },
    #     {
    #         "user_id": 10,
    #         "username": "ktaylor",
    #         "ip": "192.168.1.19",
    #         "logs": [
    #             {
    #                 "url": "http://ebay.com",
    #                 "response": 200,
    #                 "request_count": 34,
    #                 "data_transmitted": 1024000,
    #             },
    #         ],
    #         "total_requests": 34,
    #         "total_data": 1024000,
    #     },
    #     {
    #         "user_id": 11,
    #         "username": "rthomas",
    #         "ip": "192.168.1.20",
    #         "logs": [
    #             {
    #                 "url": "http://reddit.com",
    #                 "response": 200,
    #                 "request_count": 112,
    #                 "data_transmitted": 6144000,
    #             },
    #         ],
    #         "total_requests": 112,
    #         "total_data": 6144000,
    #     },
    #     {
    #         "user_id": 12,
    #         "username": "dwhite",
    #         "ip": "192.168.1.21",
    #         "logs": [
    #             {
    #                 "url": "http://instagram.com",
    #                 "response": 200,
    #                 "request_count": 89,
    #                 "data_transmitted": 4608000,
    #             },
    #         ],
    #         "total_requests": 89,
    #         "total_data": 4608000,
    #     },
    #     {
    #         "user_id": 13,
    #         "username": "jharris",
    #         "ip": "192.168.1.22",
    #         "logs": [
    #             {
    #                 "url": "http://pinterest.com",
    #                 "response": 200,
    #                 "request_count": 45,
    #                 "data_transmitted": 2048000,
    #             },
    #         ],
    #         "total_requests": 45,
    #         "total_data": 2048000,
    #     },
    #     {
    #         "user_id": 14,
    #         "username": "cmartin",
    #         "ip": "192.168.1.23",
    #         "logs": [
    #             {
    #                 "url": "http://netflix.com",
    #                 "response": 200,
    #                 "request_count": 234,
    #                 "data_transmitted": 15360000,
    #             },
    #         ],
    #         "total_requests": 234,
    #         "total_data": 15360000,
    #     },
    #     {
    #         "user_id": 15,
    #         "username": "sthompson",
    #         "ip": "192.168.1.24",
    #         "logs": [
    #             {
    #                 "url": "http://twitch.tv",
    #                 "response": 200,
    #                 "request_count": 167,
    #                 "data_transmitted": 9216000,
    #             },
    #         ],
    #         "total_requests": 167,
    #         "total_data": 9216000,
    #     },
    #     {
    #         "user_id": 16,
    #         "username": "bgarcia",
    #         "ip": "192.168.1.25",
    #         "logs": [
    #             {
    #                 "url": "http://dropbox.com",
    #                 "response": 200,
    #                 "request_count": 56,
    #                 "data_transmitted": 2560000,
    #             },
    #         ],
    #         "total_requests": 56,
    #         "total_data": 2560000,
    #     },
    #     {
    #         "user_id": 17,
    #         "username": "kmartinez",
    #         "ip": "192.168.1.26",
    #         "logs": [
    #             {
    #                 "url": "http://slack.com",
    #                 "response": 200,
    #                 "request_count": 134,
    #                 "data_transmitted": 5632000,
    #             },
    #         ],
    #         "total_requests": 134,
    #         "total_data": 5632000,
    #     },
    #     {
    #         "user_id": 18,
    #         "username": "pjohnson",
    #         "ip": "192.168.1.27",
    #         "logs": [
    #             {
    #                 "url": "http://zoom.us",
    #                 "response": 200,
    #                 "request_count": 89,
    #                 "data_transmitted": 3584000,
    #             },
    #         ],
    #         "total_requests": 89,
    #         "total_data": 3584000,
    #     },
    #     {
    #         "user_id": 19,
    #         "username": "dlindsey",
    #         "ip": "192.168.1.28",
    #         "logs": [
    #             {
    #                 "url": "http://atlassian.com",
    #                 "response": 200,
    #                 "request_count": 67,
    #                 "data_transmitted": 2560000,
    #             },
    #         ],
    #         "total_requests": 67,
    #         "total_data": 2560000,
    #     },
    #     {
    #         "user_id": 20,
    #         "username": "ewalker",
    #         "ip": "192.168.1.29",
    #         "logs": [
    #             {
    #                 "url": "http://notion.so",
    #                 "response": 200,
    #                 "request_count": 45,
    #                 "data_transmitted": 1536000,
    #             },
    #         ],
    #         "total_requests": 45,
    #         "total_data": 1536000,
    #     },
    # ]

    # # Filtrar por búsqueda si se proporciona
    # if search:
    #     search_lc = search.lower()
    #     filtered_users = [u for u in sample_users if search_lc in u["username"].lower()]
    # else:
    #     filtered_users = sample_users

    # # Calcular total y paginación
    # total = len(filtered_users)
    # total_pages = (total + per_page - 1) // per_page if per_page else 1

    # # Aplicar paginación
    # offset = (page - 1) * per_page
    # if per_page:
    #     paginated_users = filtered_users[offset : offset + per_page]
    # else:
    #     paginated_users = filtered_users

    # return {
    #     "users": paginated_users,
    #     "total": total,
    #     "page": page,
    #     "per_page": per_page,
    #     "total_pages": total_pages,
    # }

    try:
        if not date_suffix:
            date_suffix = datetime.now().strftime("%Y%m%d")
        if not validate_date_suffix(date_suffix):
            logger.error(f"Invalid date suffix: {date_suffix}")
            return {
                "users": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
            }

        UserModel = get_dynamic_model(db, "user", date_suffix)
        LogModel = get_dynamic_model(db, "log", date_suffix)

        if not UserModel or not LogModel:
            logger.error(f"Dynamic tables not available for date {date_suffix}")
            return {
                "users": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
            }

        # Contar total de usuarios distintos (con filtro opcional de búsqueda)
        base_filter = [UserModel.username != "-"]
        if search:
            search_lc = f"%{search.lower()}%"
            base_filter.append(func.lower(UserModel.username).like(search_lc))
        total = db.query(UserModel).filter(*base_filter).count()

        # Paginación
        offset = (page - 1) * per_page
        users_query = db.query(UserModel).filter(*base_filter).order_by(UserModel.id)
        if per_page:
            users_query = users_query.offset(offset).limit(per_page)
        users = users_query.all()

        users_map = {}
        user_ids = [u.id for u in users]

        # Traer logs solo de los usuarios de la página
        logs_query = (
            db.query(
                UserModel.id.label("user_id"),
                UserModel.username,
                UserModel.ip,
                LogModel.url,
                LogModel.response,
                LogModel.request_count,
                LogModel.data_transmitted,
            )
            .join(LogModel, UserModel.id == LogModel.user_id)
            .filter(UserModel.id.in_(user_ids))
        )

        for row in logs_query:
            user_id = row.user_id
            if user_id not in users_map:
                users_map[user_id] = {
                    "user_id": user_id,
                    "username": row.username,
                    "ip": row.ip,
                    "logs": [],
                    "total_requests": 0,
                    "total_data": 0,
                }
            log_entry = {
                "url": row.url,
                "response": row.response,
                "request_count": row.request_count,
                "data_transmitted": row.data_transmitted,
            }
            users_map[user_id]["logs"].append(log_entry)
            users_map[user_id]["total_requests"] += row.request_count
            users_map[user_id]["total_data"] += row.data_transmitted

        total_pages = (total + per_page - 1) // per_page if per_page else 1
        return {
            "users": list(users_map.values()),
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    except Exception as e:
        logger.error(f"Error in paginated get_users_logs: {str(e)}", exc_info=True)
        return {
            "users": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "total_pages": 0,
        }
    finally:
        db.close()


def get_users_with_logs_by_date(db: Session, date_suffix: str) -> list[dict[str, Any]]:
    # Validar sufijo de fecha
    if not validate_date_suffix(date_suffix):
        logger.error(f"Invalid date suffix: {date_suffix}")
        return []

    return get_users_logs(db, date_suffix)


def get_metrics_for_date(selected_date: date):
    session = get_session()
    date_suffix = selected_date.strftime("%Y%m%d")
    try:
        User, Log = get_dynamic_models(date_suffix)
    except Exception:
        # Si no existen tablas para esa fecha, devuelve métricas vacías
        return {
            "total_stats": {
                "total_users": 0,
                "total_log_entries": 0,
                "total_data_transmitted": 0,
                "total_requests": 0,
            },
            "top_users_by_activity": [],
            "top_users_by_data_transferred": [],
            "http_response_distribution_chart": {
                "labels": [],
                "data": [],
                "colors": [],
            },
            "top_pages": [],
            "users_per_ip": [],
        }

    # Total stats
    total_users = session.query(func.count(User.id)).scalar() or 0
    total_log_entries = session.query(func.count(Log.id)).scalar() or 0
    total_data_transmitted = (
        session.query(func.coalesce(func.sum(Log.data_transmitted), 0)).scalar() or 0
    )
    total_requests = (
        session.query(func.coalesce(func.sum(Log.request_count), 0)).scalar() or 0
    )

    # Top 20 users by activity
    top_users_by_activity = (
        session.query(User.username, func.sum(Log.request_count).label("total_visits"))
        .join(Log, Log.user_id == User.id)
        .group_by(User.username)
        .order_by(func.sum(Log.request_count).desc())
        .limit(20)
        .all()
    )
    top_users_by_activity = [
        {"username": u.username, "total_visits": u.total_visits}
        for u in top_users_by_activity
    ]

    # Top 20 users by data transferred
    top_users_by_data_transferred = (
        session.query(
            User.username, func.sum(Log.data_transmitted).label("total_data_bytes")
        )
        .join(Log, Log.user_id == User.id)
        .group_by(User.username)
        .order_by(func.sum(Log.data_transmitted).desc())
        .limit(20)
        .all()
    )
    top_users_by_data_transferred = [
        {"username": u.username, "total_data_bytes": u.total_data_bytes}
        for u in top_users_by_data_transferred
    ]

    # HTTP response distribution
    http_codes = (
        session.query(Log.response, func.count(Log.id)).group_by(Log.response).all()
    )
    code_labels = [str(code) for code, _ in http_codes]
    code_data = [count for _, count in http_codes]
    code_colors = [
        (
            "#3B82F6"
            if 200 <= int(code) < 300
            else (
                "#F59E0B"
                if 300 <= int(code) < 400
                else (
                    "#EF4444"
                    if 400 <= int(code) < 500
                    else "#8B5CF6" if 500 <= int(code) < 600 else "#10B981"
                )
            )
        )
        for code in code_labels
    ]

    # Top 20 pages
    top_pages = (
        session.query(
            Log.url,
            func.sum(Log.request_count).label("total_requests"),
            func.count(func.distinct(Log.user_id)).label("unique_visits"),
            func.sum(Log.data_transmitted).label("total_data_bytes"),
        )
        .group_by(Log.url)
        .order_by(func.sum(Log.request_count).desc())
        .limit(20)
        .all()
    )
    top_pages = [
        {
            "url": p.url,
            "total_requests": p.total_requests,
            "unique_visits": p.unique_visits,
            "total_data_bytes": p.total_data_bytes,
        }
        for p in top_pages
    ]

    # IPs compartidas por múltiples usuarios
    users_per_ip = (
        session.query(
            User.ip,
            func.count(User.id).label("user_count"),
            get_concat_function(User.username, ", ").label("usernames"),
        )
        .group_by(User.ip)
        .having(func.count(User.id) > 1)
        .all()
    )
    users_per_ip = [
        {"ip": ip.ip, "user_count": ip.user_count, "usernames": ip.usernames}
        for ip in users_per_ip
    ]

    return {
        "total_stats": {
            "total_users": total_users,
            "total_log_entries": total_log_entries,
            "total_data_transmitted": total_data_transmitted,
            "total_requests": total_requests,
        },
        "top_users_by_activity": top_users_by_activity,
        "top_users_by_data_transferred": top_users_by_data_transferred,
        "http_response_distribution_chart": {
            "labels": code_labels,
            "data": code_data,
            "colors": code_colors,
        },
        "top_pages": top_pages,
        "users_per_ip": users_per_ip,
    }
