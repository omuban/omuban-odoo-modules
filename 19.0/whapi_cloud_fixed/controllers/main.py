# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

from odoo import http, fields
from odoo.http import request

from . import extractor

_logger = logging.getLogger(__name__)


def _get_expected_token():
    try:
        return request.env['ir.config_parameter'].sudo().get_param('omu.wa.api.key') or None
    except Exception:
        return None


@http.route(['/whapi/webhook', '/whapi/webhook/messages'], type='http', auth='public', methods=['GET'], csrf=False)
def _health_get():
    # simple health endpoint for GET
    return request.make_response(json.dumps({"status": "ok"}), headers=[('Content-Type', 'application/json')])


class WhapiController(http.Controller):

    @http.route(['/whapi/webhook', '/whapi/webhook/messages'], type='http', auth='public', methods=['POST'], csrf=False)
    def whapi_webhook(self, **kwargs):
        # read raw body
        try:
            body = request.httprequest.get_data(as_text=True) or ''
            payload = json.loads(body) if body else {}
        except Exception:
            # if JSON parsing fails, keep raw text
            payload = body or {}

        # Debug log (do not log tokens)
        try:
            hdrs = request.httprequest.headers
            interesting = {
                'X-Whapi-Token': hdrs.get('X-Whapi-Token'),
                'Authorization': hdrs.get('Authorization') or hdrs.get('authorization'),
                'Content-Type': hdrs.get('Content-Type')
            }
            _logger.info("WHAPI incoming headers: %s", interesting)
        except Exception:
            _logger.exception("Failed to read headers")

        # Token check (if configured)
        expected = _get_expected_token()
        if expected:
            header_token = request.httprequest.headers.get('X-Whapi-Token')
            auth_header = request.httprequest.headers.get('Authorization') or request.httprequest.headers.get('authorization')
            auth_token = None
            if auth_header:
                parts = auth_header.split()
                if len(parts) >= 2 and parts[0].lower() == 'bearer':
                    auth_token = parts[1]
                else:
                    auth_token = parts[-1]
            query_token = request.params.get('token')

            # body_token: tolerant to payload being dict or list
            body_token = None
            try:
                if isinstance(payload, dict):
                    body_token = payload.get('token') or payload.get('access_token')
                elif isinstance(payload, list) and payload:
                    # try first element if it's a dict
                    first = payload[0]
                    if isinstance(first, dict):
                        body_token = first.get('token') or first.get('access_token')
            except Exception:
                body_token = None

            token = header_token or auth_token or query_token or body_token
            if not token or token != expected:
                _logger.warning("WHAPI invalid token (incoming=%s)", bool(token))
                return request.make_response(
                    json.dumps({"status": "error", "message": "invalid token"}),
                    headers=[('Content-Type', 'application/json')],
                    status=401
                )

        # Accept payload as dict or list. We'll normalize to a list of items to process.
        items_to_process = []
        if isinstance(payload, list):
            items_to_process = payload
        elif isinstance(payload, dict):
            # Some webhook providers wrap messages under a key, e.g. {'messages': [...]}
            # Try to detect and expand common wrapper keys
            if 'messages' in payload and isinstance(payload.get('messages'), list):
                items_to_process = payload.get('messages')
            else:
                items_to_process = [payload]
        else:
            # payload is raw string or unknown; pass it to extractor as-is
            items_to_process = [payload]

        created_ids = []
        errors = []

        # Process each incoming item (defensive, per-item errors won't stop others)
        for idx, item in enumerate(items_to_process):
            try:
                # extractor may accept raw payload or dict; it may also return dict or list
                info = extractor.extract_whapi_payload(item)

                # If extractor returned a list (multiple messages inside item), flatten them
                infos = info if isinstance(info, list) else [info]

                for info_obj in infos:
                    if not isinstance(info_obj, dict):
                        _logger.warning("whapi: extractor returned non-dict info: %r", info_obj)
                        continue

                    # If recipient missing, read configured own number
                    recipient = info_obj.get('recipient')
                    if not recipient:
                        try:
                            cfg = request.env['ir.config_parameter'].sudo().get_param('omu.wa.number')
                            if cfg:
                                recipient = extractor.normalize_phone(cfg)
                        except Exception:
                            recipient = None

                    # Determine message_type safely (if original item is dict and has event)
                    message_type = None
                    if isinstance(item, dict):
                        try:
                            ev = item.get('event')
                            if isinstance(ev, dict):
                                message_type = ev.get('type')
                        except Exception:
                            message_type = None

                    # prepare values
                    vals = {
                        'name': info_obj.get('message_id') or str(datetime.utcnow()),
                        'sender': info_obj.get('sender'),
                        'recipient': recipient,
                        'chat_id': info_obj.get('chat_id'),
                        'from_name': info_obj.get('from_name'),
                        'chat_name': info_obj.get('chat_name'),
                        'text': info_obj.get('text'),
                        'quoted_id': info_obj.get('quoted_id'),
                        'quoted_author': info_obj.get('quoted_author'),
                        'quoted_text': info_obj.get('quoted_text'),
                        'status': info_obj.get('status'),
                        'from_me': bool(info_obj.get('from_me')),
                        'payload': json.dumps(item) if isinstance(item, dict) else str(item),
                        # info_obj['received_at'] should already be Odoo-compatible string (extractor ensures that)
                        'received_at': info_obj.get('received_at') or fields.Datetime.now(),
                        'message_type': message_type,
                        'channel_id': info_obj.get('channel_id'),
                        # pass through possible pre-extracted wa fields from extractor
                        'wa_category': info_obj.get('wa_category'),
                        'wa_tags': info_obj.get('wa_tags'),
                    }

                    # create record (use sudo as webhook typically needs to bypass ACL)
                    rec = request.env['whapi.message'].sudo().create(vals)
                    created_ids.append(rec.id)

            except Exception as exc:
                # Log but continue processing remaining items
                _logger.exception("Failed to process webhook item #%s: %s", idx, exc)
                errors.append({"index": idx, "error": str(exc)})

        # Return result summary
        result = {"status": "ok", "created": created_ids, "errors": errors}
        status_code = 200 if not errors else 207  # 207 Multi-Status (partial success)
        return request.make_response(json.dumps(result), headers=[('Content-Type', 'application/json')], status=status_code)
