"""FlowValidationService — validates flow definitions before publishing.

Validation covers two categories:

1. Graph validation
   - Exactly one Trigger node
   - At least one End node
   - No orphan / disconnected nodes
   - Trigger must be able to reach an End node
   - All nodes reachable from the Trigger
   - No cycles

2. Node configuration validation
   - Delay / Wait: duration > 0
   - Send WhatsApp: template_id or template_name required
   - Send Email: subject required; template_id or template_name required
   - Notification: title and message required
   - Condition: field, operator and value required
"""

from typing import Any, Dict, List


class FlowValidationService:

    @staticmethod
    def validate(definition: Dict[str, Any]) -> Dict[str, Any]:
        nodes = definition.get("nodes") or []
        edges = definition.get("edges") or []

        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        node_map = {n["id"]: n for n in nodes}

        # Build adjacency: source -> [targets]
        adjacency: Dict[str, list] = {}
        incoming: Dict[str, list] = {}
        for edge in edges:
            src = edge.get("from") or edge.get("source")
            tgt = edge.get("to") or edge.get("target")
            if src and tgt:
                adjacency.setdefault(src, []).append(tgt)
                incoming.setdefault(tgt, []).append(src)

        node_ids = set(node_map.keys())
        edge_srcs = set(adjacency.keys())
        edge_tgts = set(incoming.keys())

        # ── 1. Exactly one Trigger ─────────────────────────────────
        trigger_nodes = [n for n in nodes if n.get("type") == "trigger"]
        if len(trigger_nodes) == 0:
            errors.append(_graph_error("Flow must have exactly one Trigger node"))
        elif len(trigger_nodes) > 1:
            for n in trigger_nodes:
                errors.append(_graph_error(
                    f"Trigger node '{_label(n)}' — only one Trigger is allowed",
                    node_id=n["id"],
                ))

        trigger_id = trigger_nodes[0]["id"] if len(trigger_nodes) == 1 else None

        # ── 2. At least one End ────────────────────────────────────
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if len(end_nodes) == 0:
            errors.append(_graph_error("Flow must have at least one End node"))

        # ── 3. No orphan / disconnected nodes ──────────────────────
        for node in nodes:
            nid = node["id"]
            ntype = node["type"]
            lbl = _label(node)
            has_in = nid in incoming and len(incoming[nid]) > 0
            has_out = nid in adjacency and len(adjacency[nid]) > 0

            if ntype == "trigger":
                if not has_out:
                    errors.append(_graph_error(
                        f"Trigger '{lbl}' must have at least one outgoing connection",
                        node_id=nid,
                    ))
            elif ntype == "end":
                if not has_in:
                    warnings.append(_graph_warning(
                        f"End '{lbl}' has no incoming connections",
                        node_id=nid,
                    ))
            else:
                if not has_in and not has_out:
                    errors.append(_graph_error(
                        f"Node '{lbl}' is completely disconnected",
                        node_id=nid,
                    ))
                elif not has_in:
                    errors.append(_graph_error(
                        f"Node '{lbl}' has no incoming connections",
                        node_id=nid,
                    ))
                elif not has_out:
                    errors.append(_graph_error(
                        f"Node '{lbl}' has no outgoing connections",
                        node_id=nid,
                    ))

        # ── 4 & 7. All nodes reachable from Trigger (BFS) ──────────
        if trigger_id:
            visited = set()
            queue = [trigger_id]
            while queue:
                nid = queue.pop(0)
                if nid in visited:
                    continue
                visited.add(nid)
                for nxt in adjacency.get(nid, []):
                    queue.append(nxt)

            unreachable = node_ids - visited
            if trigger_id in unreachable:
                unreachable.discard(trigger_id)
            for nid in sorted(unreachable, key=lambda x: _label(node_map.get(x, {}))):
                n = node_map.get(nid, {})
                errors.append(_graph_error(
                    f"Node '{_label(n)}' is not reachable from the Trigger",
                    node_id=nid,
                ))

            # ── 5. Trigger can reach at least one End ──────────────
            reachable_ends = [n for n in end_nodes if n["id"] in visited]
            if end_nodes and not reachable_ends:
                errors.append(_graph_error(
                    "Trigger cannot reach any End node — the flow will never terminate"
                ))

            # ── 6. No cycles (DFS) ─────────────────────────────────
            visited_dfs: set = set()
            rec_stack: set = set()
            has_cycle_flag = False

            def _dfs(nid: str) -> bool:
                nonlocal has_cycle_flag
                visited_dfs.add(nid)
                rec_stack.add(nid)
                for nxt in adjacency.get(nid, []):
                    if nxt not in visited_dfs:
                        if _dfs(nxt):
                            return True
                    elif nxt in rec_stack:
                        has_cycle_flag = True
                        return True
                rec_stack.discard(nid)
                return False

            # Run DFS from trigger
            _dfs(trigger_id)
            # Check any remaining unvisited components
            for nid in list(adjacency.keys()):
                if nid not in visited_dfs:
                    _dfs(nid)

            if has_cycle_flag:
                errors.append(_graph_error("Flow contains a cycle — infinite loop detected"))

        # ── Node configuration validation ──────────────────────────
        for node in nodes:
            nid = node["id"]
            ntype = node["type"]
            config = node.get("config") or {}
            lbl = _label(node)

            if ntype == "delay":
                mode = config.get("mode", "fixed")
                if mode == "relative_to_lead_date":
                    if not config.get("lead_date_field"):
                        errors.append(_node_error(
                            f"Delay '{lbl}' (relative to lead date) requires a lead date field",
                            node_id=nid,
                        ))
                    if config.get("offset_unit") not in ("minutes", "hours", "days", "weeks"):
                        errors.append(_node_error(
                            f"Delay '{lbl}' (relative to lead date) requires a valid offset unit",
                            node_id=nid,
                        ))
                else:
                    # Fixed mode (default — every existing saved Delay node
                    # with no "mode" key at all validates exactly as before).
                    duration = config.get("duration", 0)
                    if not isinstance(duration, (int, float)) or duration <= 0:
                        errors.append(_node_error(
                            f"Delay '{lbl}' must have duration greater than 0",
                            node_id=nid,
                        ))

            elif ntype == "wait":
                wait_type = config.get("wait_type", "duration")
                if wait_type == "specific_datetime":
                    if not config.get("target_datetime") and not config.get("target_lead_field"):
                        errors.append(_node_error(
                            f"Wait '{lbl}' (specific date/time) requires a target datetime or lead date field",
                            node_id=nid,
                        ))
                elif wait_type in ("stage_changed", "field_condition"):
                    if not config.get("field"):
                        errors.append(_node_error(
                            f"Wait '{lbl}' requires a field to watch",
                            node_id=nid,
                        ))
                    if not config.get("operator"):
                        errors.append(_node_error(
                            f"Wait '{lbl}' requires an operator",
                            node_id=nid,
                        ))
                    if not config.get("value"):
                        errors.append(_node_error(
                            f"Wait '{lbl}' requires a value",
                            node_id=nid,
                        ))
                elif wait_type == "manual_approval":
                    # Mirrors the standalone Approval node's own validation
                    # below — same required fields, same contract.
                    if not config.get("approver"):
                        errors.append(_node_error(
                            f"Wait '{lbl}' (manual approval) requires an approver",
                            node_id=nid,
                        ))
                    if not config.get("title"):
                        errors.append(_node_error(
                            f"Wait '{lbl}' (manual approval) requires a title",
                            node_id=nid,
                        ))
                elif wait_type == "webhook_event":
                    if not config.get("event_key"):
                        errors.append(_node_error(
                            f"Wait '{lbl}' (external webhook/event) requires an event key",
                            node_id=nid,
                        ))
                elif wait_type == "replied":
                    # channel defaults to "whatsapp" — nothing required. An
                    # optional timeout (falls through to a timeout branch if
                    # the lead never replies) needs both single next-node
                    # targets so ExecutionEngine._resume_from knows which one
                    # edge to take on resume — see wait_executor.py's
                    # docstring. A plain "replied" Wait with no timeout is
                    # untouched by this check.
                    if config.get("timeout") and not (
                        config.get("replied_next_node_id") and config.get("timeout_next_node_id")
                    ):
                        errors.append(_node_error(
                            f"Wait '{lbl}' (replied, with timeout) requires both a "
                            f"replied_next_node_id and a timeout_next_node_id",
                            node_id=nid,
                        ))
                else:
                    # "duration" (default — every existing saved Wait node
                    # with no "wait_type" key at all validates exactly as
                    # before).
                    duration = config.get("duration", 0)
                    if not isinstance(duration, (int, float)) or duration <= 0:
                        errors.append(_node_error(
                            f"Wait '{lbl}' must have duration greater than 0",
                            node_id=nid,
                        ))

            elif ntype == "send_whatsapp":
                # Accepts EITHER field: the Properties Panel's template
                # picker (PropertiesPanel.jsx TemplateSelectField) stores
                # the selected template's id under template_id — checking
                # template_name only (the old check) meant a template
                # selected through the actual dropdown never validated,
                # since that field was never populated by the UI at all.
                # template_name alone is also still accepted so any
                # existing journey/API caller using the legacy free-text
                # convention (see send_whatsapp_executor.py's fallback)
                # keeps validating unchanged.
                if not config.get("template_id") and not config.get("template_name"):
                    errors.append(_node_error(
                        f"Send WhatsApp '{lbl}' requires a template (select one from the dropdown)",
                        node_id=nid,
                    ))

            elif ntype == "send_email":
                if not config.get("subject"):
                    errors.append(_node_error(
                        f"Send Email '{lbl}' requires a subject",
                        node_id=nid,
                    ))
                # Same template_id/template_name acceptance as send_whatsapp
                # above — matches what the UI actually stores and what
                # send_email_executor.py already accepts.
                if not config.get("template_id") and not config.get("template_name"):
                    errors.append(_node_error(
                        f"Send Email '{lbl}' requires a template (select one from the dropdown)",
                        node_id=nid,
                    ))

            elif ntype == "notification":
                if not config.get("title"):
                    errors.append(_node_error(
                        f"Notification '{lbl}' requires a title",
                        node_id=nid,
                    ))
                if not config.get("message"):
                    errors.append(_node_error(
                        f"Notification '{lbl}' requires a message",
                        node_id=nid,
                    ))

            elif ntype == "update_lead":
                if not config.get("lead_field"):
                    errors.append(_node_error(
                        f"Update Lead '{lbl}' requires a lead field name",
                        node_id=nid,
                    ))
                if not config.get("value"):
                    errors.append(_node_error(
                        f"Update Lead '{lbl}' requires a value",
                        node_id=nid,
                    ))

            elif ntype == "update_company":
                if not config.get("company_field"):
                    errors.append(_node_error(
                        f"Update Company '{lbl}' requires a company field name",
                        node_id=nid,
                    ))
                if not config.get("value"):
                    errors.append(_node_error(
                        f"Update Company '{lbl}' requires a value",
                        node_id=nid,
                    ))

            elif ntype == "assign_owner":
                if not config.get("owner_id"):
                    errors.append(_node_error(
                        f"Assign Owner '{lbl}' requires an owner ID",
                        node_id=nid,
                    ))

            elif ntype == "change_lead_stage":
                if not config.get("target_stage"):
                    errors.append(_node_error(
                        f"Change Lead Stage '{lbl}' requires a target stage",
                        node_id=nid,
                    ))

            elif ntype == "create_crm_task":
                if not config.get("title"):
                    errors.append(_node_error(
                        f"Create CRM Task '{lbl}' requires a title",
                        node_id=nid,
                    ))

            elif ntype == "create_note":
                if not config.get("note"):
                    errors.append(_node_error(
                        f"Create Note '{lbl}' requires note content",
                        node_id=nid,
                    ))

            elif ntype == "approval":
                if not config.get("approver"):
                    errors.append(_node_error(
                        f"Approval '{lbl}' requires an approver",
                        node_id=nid,
                    ))
                if not config.get("title"):
                    errors.append(_node_error(
                        f"Approval '{lbl}' requires a title",
                        node_id=nid,
                    ))

            elif ntype == "manual_task":
                if not config.get("assignee"):
                    errors.append(_node_error(
                        f"Manual Task '{lbl}' requires an assignee",
                        node_id=nid,
                    ))
                if not config.get("title"):
                    errors.append(_node_error(
                        f"Manual Task '{lbl}' requires a title",
                        node_id=nid,
                    ))

            elif ntype == "condition":
                if not config.get("field"):
                    errors.append(_node_error(
                        f"Condition '{lbl}' requires a field",
                        node_id=nid,
                    ))
                if not config.get("operator"):
                    errors.append(_node_error(
                        f"Condition '{lbl}' requires an operator",
                        node_id=nid,
                    ))
                if not config.get("value"):
                    errors.append(_node_error(
                        f"Condition '{lbl}' requires a value",
                        node_id=nid,
                    ))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


def _label(node: Dict[str, Any]) -> str:
    return node.get("label") or node.get("id", "unknown")


def _graph_error(msg: str, node_id: str = None) -> Dict[str, Any]:
    return {"type": "graph", "node_id": node_id, "message": msg}


def _graph_warning(msg: str, node_id: str = None) -> Dict[str, Any]:
    return {"type": "graph", "node_id": node_id, "message": msg}


def _node_error(msg: str, node_id: str = None) -> Dict[str, Any]:
    return {"type": "node", "node_id": node_id, "message": msg}
