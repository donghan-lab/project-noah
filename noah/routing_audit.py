"""M12's bounded operational routing audit; no Task or Evidence ownership."""

import re

import psycopg


_SAFE_CODE = re.compile(r"[A-Za-z0-9_.-]{1,80}\Z")


class AuditWriteError(Exception):
    def __init__(self, uncertain=False):
        self.uncertain = uncertain
        super().__init__("Routing audit outcome is unconfirmed" if uncertain
                         else "Routing audit write failed")


def safe_code(value):
    """Only bounded symbolic result codes enter the operational row."""
    return value if isinstance(value, str) and _SAFE_CODE.fullmatch(value) else "UNSPECIFIED"


class RoutingAudit:
    def __init__(self, connection_factory):
        self.connection_factory = connection_factory

    def _write(self, sql, params):
        try:
            db = self.connection_factory()
        except (psycopg.Error, OSError, ValueError) as error:
            raise AuditWriteError() from error  # No transaction was opened.
        try:
            result = db.execute(sql, params)
            if result.rowcount != 1:
                raise AuditWriteError()
            db.commit()
        except AuditWriteError:
            try:
                db.rollback()
            except (psycopg.Error, OSError):
                pass
            raise
        except (psycopg.OperationalError, psycopg.InterfaceError, OSError) as error:
            raise AuditWriteError(uncertain=True) from error
        except (psycopg.Error, ValueError) as error:
            try:
                db.rollback()
            except (psycopg.Error, OSError):
                pass
            raise AuditWriteError() from error
        finally:
            try:
                db.close()
            except (psycopg.Error, OSError):
                pass

    def reserve(self, router_id, actor_user_id):
        self._write("""INSERT INTO noah.routing_audit(router_id,actor_user_id,stage)
            VALUES(%s,%s,'reserved')""", (router_id, actor_user_id))

    def route_validated(self, router_id, route):
        self._write("""UPDATE noah.routing_audit SET stage='route_validated',
            validated_route=%s, updated_at=now()
            WHERE router_id=%s AND stage='reserved'""", (route, router_id))

    def dispatch_prepared(self, router_id, route):
        self._write("""UPDATE noah.routing_audit SET stage='dispatch_prepared',
            dispatch_prepared=true, delegate_capability=%s, updated_at=now()
            WHERE router_id=%s AND stage='route_validated' AND validated_route=%s""",
            (route, router_id, route))

    def observed(self, router_id, prior_stage, observation_class, http_status,
                 outcome_code, delegate_result_observed=False, delegate_request_id=None,
                 delegate_task_id=None, delegate_execution_id=None):
        self._write("""UPDATE noah.routing_audit SET stage='observed',
            delegate_result_observed=%s, delegate_request_id=%s,
            delegate_task_id=%s, delegate_execution_id=%s,
            observation_class=%s, http_status=%s, outcome_code=%s,
            observed_at=now(), updated_at=now()
            WHERE router_id=%s AND stage=%s""",
            (delegate_result_observed, delegate_request_id, delegate_task_id,
             delegate_execution_id, observation_class, http_status,
             safe_code(outcome_code), router_id, prior_stage))
