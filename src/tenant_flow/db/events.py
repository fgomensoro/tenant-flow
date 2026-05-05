from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


class TenantContextError(SQLAlchemyError):
    """Raised when a connection is used without tenant context set."""


@event.listens_for(Engine, "before_cursor_execute")
def verify_tenant_context(conn, cursor, statement, parameters, context, executemany):
    # Permitir queries de control internas
    statement_upper = statement.strip().upper()
    control_prefixes = ("SET", "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE", "SHOW")
    if statement_upper.startswith(control_prefixes):
        return

    if "SET_CONFIG" in statement_upper:
        return

    # Verificar que app.current_tenant esté seteado
    try:
        cursor.execute("SHOW app.current_tenant")
        result = cursor.fetchone()
        tenant_value = result[0] if result else None
    except Exception as e:
        # Cualquier error en SHOW = variable no existe = falta tenant context
        raise TenantContextError(
            "Connection used without tenant context. Did you forget Depends(get_tenant_session)?"
        ) from e

    if not tenant_value:
        raise TenantContextError(
            "Connection used without tenant context. Did you forget Depends(get_tenant_session)?"
        )
