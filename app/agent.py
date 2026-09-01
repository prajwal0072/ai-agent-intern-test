import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from app.order_tool import lookup_order
from app.retrieval import Retriever
from app.session import Session


# ============================================================
# OBSERVABILITY
# ============================================================

logger = logging.getLogger("aster_row.agent")

if not logger.handlers:
    handler = logging.FileHandler(
        "agent_trace.jsonl",
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_trace(
    event: str,
    **data: Any,
) -> None:
    """
    Write a structured JSON trace.

    Never log secrets or sensitive customer information.
    """

    safe_data = {
        "event": event,
        **data,
    }

    logger.info(
        json.dumps(
            safe_data,
            ensure_ascii=False,
            default=str,
        )
    )


# ============================================================
# RESPONSE
# ============================================================

@dataclass
class AgentResponse:
    answer: str
    sources: list[str]
    handoff: bool = False
    tool_used: bool = False


# ============================================================
# ORDER DETECTION
# ============================================================

ORDER_ID_PATTERN = re.compile(
    r"\bORD-[A-Z0-9]+\b",
    re.IGNORECASE,
)


def extract_order_id(
    text: str,
) -> str | None:

    match = ORDER_ID_PATTERN.search(text)

    if not match:
        return None

    return match.group(0).upper()


def is_order_question(
    text: str,
) -> bool:

    text_lower = text.lower()

    # An explicit order ID always means
    # that the user is referring to an order.
    if extract_order_id(text):
        return True

    order_terms = [
        "order",
        "delivery",
        "delivered",
        "shipping status",
        "tracking",
        "where is",
        "when will",
        "arrive",
        "check",
    ]

    return any(
        term in text_lower
        for term in order_terms
    )


# ============================================================
# POLICY DETECTION
# ============================================================

def is_policy_question(
    text: str,
) -> bool:

    text_lower = text.lower()

    policy_terms = [
        "return",
        "refund",
        "warranty",
        "ship",
        "shipping",
        "cancel",
        "cancellation",
        "international",
        "canada",
        "final sale",
        "gift card",
        "membership",
    ]

    return any(
        term in text_lower
        for term in policy_terms
    )


# ============================================================
# PRIVACY / INTERNAL INFORMATION
# ============================================================

def asks_for_internal_information(
    text: str,
) -> bool:

    text_lower = text.lower()

    forbidden_terms = [
        "system prompt",
        "system instructions",
        "hidden instructions",
        "developer prompt",
        "api key",
        "secret",
        "risk score",
        "internal note",
        "warehouse note",
        "support tags",
        "customer email",
        "shipping address",
    ]

    return any(
        term in text_lower
        for term in forbidden_terms
    )


# ============================================================
# HANDOFF
# ============================================================

def needs_human_handoff(
    text: str,
) -> bool:

    text_lower = text.lower()

    return any(
        phrase in text_lower
        for phrase in [
            "human",
            "agent",
            "representative",
            "support person",
            "customer service",
        ]
    )


# ============================================================
# SUPPORT AGENT
# ============================================================

class SupportAgent:

    def __init__(
        self,
        retriever: Retriever | None = None,
    ):

        self.retriever = (
            retriever
            if retriever is not None
            else Retriever()
        )

        log_trace(
            "agent_initialized"
        )

    def handle(
        self,
        session: Session,
        user_message: str,
    ) -> AgentResponse:

        # --------------------------------------------------
        # 1. Store user message
        # --------------------------------------------------

        session.add_message(
            "user",
            user_message,
        )

        log_trace(
            "user_message",
            session_id=session.session_id,
            message=user_message,
            history_length=len(
                session.messages
            ),
            current_order_id=session.current_order_id,
            current_topic=session.current_topic,
        )

        # --------------------------------------------------
        # 2. Internal information protection
        # --------------------------------------------------

        if asks_for_internal_information(
            user_message
        ):

            answer = (
                "I can't provide system instructions, "
                "secrets, or internal-only information."
            )

            log_trace(
                "privacy_block",
                session_id=session.session_id,
            )

            session.add_message(
                "assistant",
                answer,
            )

            return AgentResponse(
                answer=answer,
                sources=[],
                handoff=False,
                tool_used=False,
            )

        # --------------------------------------------------
        # 3. Detect order ID
        # --------------------------------------------------

        order_id = extract_order_id(
            user_message
        )

        if order_id:

            session.set_order_id(
                order_id
            )

            log_trace(
                "order_id_detected",
                session_id=session.session_id,
                order_id=order_id,
            )

        # --------------------------------------------------
        # 4. Order lookup
        # --------------------------------------------------

        if (
            order_id
            or (
                session.current_order_id
                and is_order_question(
                    user_message
                )
            )
        ):

            lookup_id = (
                order_id
                or session.current_order_id
            )

            log_trace(
                "tool_call",
                session_id=session.session_id,
                tool="order_lookup",
                arguments={
                    "order_id": lookup_id,
                },
            )

            result = lookup_order(
                lookup_id
            )

            # --------------------------------------------------
            # IMPORTANT:
            # Do not log internal customer data.
            # Only log safe result metadata.
            # --------------------------------------------------

            log_trace(
                "tool_result",
                session_id=session.session_id,
                tool="order_lookup",
                found=result.get("found"),
                error=result.get("error"),
            )

            if not result["found"]:

                answer = result["message"]

                log_trace(
                    "order_lookup_failed",
                    session_id=session.session_id,
                    reason=result.get("error"),
                )

                session.add_message(
                    "assistant",
                    answer,
                )

                return AgentResponse(
                    answer=answer,
                    sources=[],
                    handoff=False,
                    tool_used=True,
                )

            order = result["order"]

            status = order["status"]

            # --------------------------------------------------
            # Exception
            # --------------------------------------------------

            if status == "exception":

                answer = (
                    f"Order {order['order_id']} "
                    "requires support review. "
                    "I recommend contacting a support "
                    "representative for assistance."
                )

                log_trace(
                    "handoff",
                    session_id=session.session_id,
                    reason="order_exception",
                )

                session.add_message(
                    "assistant",
                    answer,
                )

                return AgentResponse(
                    answer=answer,
                    sources=[],
                    handoff=True,
                    tool_used=True,
                )

            # --------------------------------------------------
            # Cancelled
            # --------------------------------------------------

            if status == "cancelled":

                answer = (
                    f"Order {order['order_id']} "
                    "is currently cancelled."
                )

                session.add_message(
                    "assistant",
                    answer,
                )

                return AgentResponse(
                    answer=answer,
                    sources=[],
                    tool_used=True,
                )

            # --------------------------------------------------
            # Returned
            # --------------------------------------------------

            if status == "returned":

                answer = (
                    f"Order {order['order_id']} "
                    "has been returned."
                )

                session.add_message(
                    "assistant",
                    answer,
                )

                return AgentResponse(
                    answer=answer,
                    sources=[],
                    tool_used=True,
                )

            # --------------------------------------------------
            # Shipped
            # --------------------------------------------------

            if status == "shipped":

                estimate = order.get(
                    "estimated_delivery"
                )

                carrier = order.get(
                    "carrier"
                )

                if estimate:

                    answer = (
                        f"Order {order['order_id']} "
                        f"has shipped."

                    )

                    if carrier:
                        answer += (
                            f" The carrier is "
                            f"{carrier}."
                        )

                    answer += (
                        f" The current estimated "
                        f"delivery is {estimate}."
                    )

                else:

                    answer = (
                        f"Order {order['order_id']} "
                        "has shipped, but an estimated "
                        "delivery date is currently "
                        "unavailable."
                    )

                session.add_message(
                    "assistant",
                    answer,
                )

                return AgentResponse(
                    answer=answer,
                    sources=[],
                    tool_used=True,
                )

            # --------------------------------------------------
            # Delivered
            # --------------------------------------------------

            if status == "delivered":

                answer = (
                    f"Order {order['order_id']} "
                    "has been delivered."
                )

                session.add_message(
                    "assistant",
                    answer,
                )

                return AgentResponse(
                    answer=answer,
                    sources=[],
                    tool_used=True,
                )

            # --------------------------------------------------
            # Other statuses
            # --------------------------------------------------

            answer = (
                f"Order {order['order_id']} "
                f"is currently {status}."
            )

            if order.get(
                "estimated_delivery"
            ):

                answer += (
                    f" The current estimated "
                    f"delivery is "
                    f"{order['estimated_delivery']}."
                )

            session.add_message(
                "assistant",
                answer,
            )

            return AgentResponse(
                answer=answer,
                sources=[],
                tool_used=True,
            )

        # --------------------------------------------------
        # 5. Knowledge-base retrieval
        # --------------------------------------------------

        if is_policy_question(
            user_message
        ):

            log_trace(
                "retrieval_start",
                session_id=session.session_id,
                query=user_message,
            )

            response = (
                self.retriever
                .search_with_conflict_detection(
                    user_message
                )
            )

            # Log metadata only.
            retrieved = []

            for result in response.results:

                retrieved.append(
                    {
                        "filename":
                            result.chunk.filename,
                        "heading":
                            result.chunk.heading,
                        "score":
                            getattr(
                                result,
                                "score",
                                None,
                            ),
                        "status":
                            result.chunk.metadata.get(
                                "status"
                            ),
                        "authority":
                            result.chunk.metadata.get(
                                "policy_authority"
                            ),
                    }
                )

            log_trace(
                "retrieval_results",
                session_id=session.session_id,
                results=retrieved,
                conflict_detected=(
                    response.conflict_detected
                ),
            )

            if not response.results:

                answer = (
                    "I don't have enough information "
                    "in the supplied company documents "
                    "to answer that reliably. "
                    "Please contact support for assistance."
                )

                log_trace(
                    "handoff",
                    session_id=session.session_id,
                    reason="insufficient_information",
                )

                session.add_message(
                    "assistant",
                    answer,
                )

                return AgentResponse(
                    answer=answer,
                    sources=[],
                    handoff=True,
                )

            # Remember topic.
            session.set_topic(
                self._infer_topic(
                    user_message
                )
            )

            top = response.results[0]

            source = (
                f"{top.chunk.filename} — "
                f"{top.chunk.heading}"
            )

            answer = (
                f"According to the supplied policy, "
                f"{top.chunk.text.strip()}"
            )

            if response.conflict_detected:

                answer += (
                    "\n\nI found multiple relevant "
                    "company documents, including "
                    "content with different document "
                    "statuses. The current authoritative "
                    "source is being prioritized; if the "
                    "documents cannot be reconciled, "
                    "support review is recommended."
                )

            answer += (
                f"\n\nSource: {source}"
            )

            log_trace(
                "final_response",
                session_id=session.session_id,
                answer=answer,
                sources=[source],
                handoff=response.conflict_detected,
                tool_used=False,
            )

            session.add_message(
                "assistant",
                answer,
            )

            return AgentResponse(
                answer=answer,
                sources=[source],
                handoff=response.conflict_detected,
            )

        # --------------------------------------------------
        # 6. Unknown / insufficient information
        # --------------------------------------------------

        answer = (
            "I don't have enough information in the "
            "supplied company documents to answer that "
            "reliably."
        )

        log_trace(
            "handoff",
            session_id=session.session_id,
            reason="unknown_or_insufficient_question",
        )

        session.add_message(
            "assistant",
            answer,
        )

        return AgentResponse(
            answer=answer,
            sources=[],
            handoff=True,
        )

    # ========================================================
    # TOPIC INFERENCE
    # ========================================================

    def _infer_topic(
        self,
        text: str,
    ) -> str:

        text_lower = text.lower()

        if (
            "international" in text_lower
            or "canada" in text_lower
        ):
            return "international_shipping"

        if "return" in text_lower:
            return "returns"

        if "refund" in text_lower:
            return "refunds"

        if "warranty" in text_lower:
            return "warranty"

        if (
            "cancel" in text_lower
            or "cancellation" in text_lower
        ):
            return "cancellation"

        return "general_policy"