# -*- coding: utf-8 -*-
import re
import logging
from datetime import datetime, timezone

from odoo import fields as odoo_fields

_logger = logging.getLogger(__name__)


# Helper: normalize phone / id to +<digits>
def normalize_phone(val):
    """
    Normalize common WA id / phone representations to +<digits>.
    Examples:
      '6285100569997' -> '+6285100569997'
      '6285100569997@s.whatsapp.net' -> '+6285100569997'
      'whatsapp:+6285100569997' -> '+6285100569997'
    Returns None if nothing found.
    """
    if not val:
        return None
    s = str(val).strip()
    # drop suffixes e.g. @s.whatsapp.net, @g.us
    s = s.split('@')[0]
    # remove common prefix
    s = s.replace('whatsapp:', '')
    # capture digits with optional leading +
    m = re.search(r'(\+?\d{6,20})', s)
    if not m:
        return None
    phone = m.group(1)
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone


def _ts_to_odoo_string(ts):
    """
    Convert integer timestamp (seconds or milliseconds) to Odoo datetime string.
    Returns None on failure.
    """
    if ts is None:
        return None
    try:
        ts_int = int(ts)
    except Exception:
        return None
    try:
        # detect ms vs s
        if ts_int > 10**12:
            ts_int = ts_int // 1000
        dt = datetime.fromtimestamp(ts_int, tz=timezone.utc)
        return odoo_fields.Datetime.to_string(dt)
    except Exception as e:
        _logger.exception("Timestamp conversion failed for %r: %s", ts, e)
        return None


def _extract_tags_from_text(text):
    """
    Return (category, tags_string)
    - find tokens like #TOKEN (multiple consecutive # handled)
    - normalize tokens to uppercase, strip surrounding non-word
    - remove duplicates while preserving order
    """
    if not text:
        return None, None
    s = str(text)
    raw_tokens = re.findall(r'#([^\s#]+)', s)
    if not raw_tokens:
        return None, None
    cleaned = []
    seen = set()
    for tok in raw_tokens:
        tok_clean = re.sub(r'^[^\w]+|[^\w]+$', '', tok, flags=re.UNICODE)
        if not tok_clean:
            continue
        tok_up = tok_clean.upper()
        if tok_up not in seen:
            seen.add(tok_up)
            cleaned.append(tok_up)
    if not cleaned:
        return None, None
    category = cleaned[0]
    tags_string = '; '.join(cleaned)
    return category, tags_string


def extract_from_message_section(m0):
    """
    Extract fields from a single message dict (messages[0]).
    Returns dict with keys:
      message_id, text, sender, chat_id, from_name, chat_name, status,
      from_me, quoted_id, quoted_author, quoted_text, received_at (Odoo string)
      and wa_category, wa_tags (if present in text).
    """
    info = {
        'message_id': None,
        'text': None,
        'sender': None,
        'chat_id': None,
        'from_name': None,
        'chat_name': None,
        'status': None,
        'from_me': False,
        'quoted_id': None,
        'quoted_author': None,
        'quoted_text': None,
        'received_at': None,
        'wa_category': None,
        'wa_tags': None,
    }

    try:
        if not isinstance(m0, dict):
            return info

        info['message_id'] = m0.get('id') or m0.get('message_id')

        # text extraction
        if m0.get('text'):
            tb = m0.get('text')
            if isinstance(tb, dict):
                info['text'] = tb.get('body') or tb.get('text')
            else:
                info['text'] = str(tb)
        else:
            info['text'] = m0.get('body') or m0.get('message') or None

        # sender candidate fields
        cand = m0.get('from') or m0.get('author') or m0.get('wa_id') or m0.get('participant')
        if cand:
            info['sender'] = normalize_phone(cand)

        # chat_id (helps detect group vs single)
        if m0.get('chat_id'):
            info['chat_id'] = m0.get('chat_id')
            # sometimes chat_id itself contains the phone; try normalize as fallback
            if not info['sender']:
                info['sender'] = normalize_phone(m0.get('chat_id'))

        # names
        info['from_name'] = m0.get('from_name') or m0.get('sender_name') or None
        info['chat_name'] = m0.get('chat_name') or m0.get('conversation_name') or None

        # status and from_me flag
        info['status'] = m0.get('status') or None
        info['from_me'] = bool(m0.get('from_me'))

        # quoted info: some providers put quoted in context or directly in message
        ctx = m0.get('context') or {}
        if isinstance(ctx, dict):
            info['quoted_id'] = ctx.get('quoted_id') or ctx.get('quotedMessageId') or None
            info['quoted_author'] = ctx.get('quoted_author') or ctx.get('quoted_author_phone') or None
            qcont = ctx.get('quoted_content') or ctx.get('quoted') or None
            if isinstance(qcont, dict):
                info['quoted_text'] = qcont.get('body') or qcont.get('text') or None

        if not info['quoted_text'] and m0.get('quoted_content'):
            qc = m0.get('quoted_content')
            if isinstance(qc, dict):
                info['quoted_text'] = qc.get('body') or qc.get('text') or None

        # timestamp -> convert to Odoo-compatible string
        ts = m0.get('timestamp') or m0.get('time') or m0.get('ts')
        info['received_at'] = _ts_to_odoo_string(ts)

        # Extract WA tags from text or quoted_text (prefer text)
        try:
            cat, tags = _extract_tags_from_text(info['text'] or info['quoted_text'] or '')
            if cat:
                info['wa_category'] = cat
            if tags:
                info['wa_tags'] = tags
        except Exception:
            _logger.exception("Error extracting WA tags in message section")

    except Exception as e:
        # Capture any unexpected error but return partial info
        _logger.exception("extract_from_message_section error: %s", e)
        # Ensure received_at at least None (already default)
    return info


def extract_whapi_payload(payload):
    """
    Top-level extractor for the incoming WHAPI payload.

    - If payload is dict with 'messages' (list), returns list of info dicts (one per message).
    - If payload is dict with single message, returns a dict (single info).
    - If payload is raw string or unknown, returns a single minimal dict.

    Returned info dict keys:
      sender, recipient, text, from_name, chat_name, received_at (Odoo str),
      message_id, quoted_id, quoted_author, quoted_text, status, from_me, chat_id,
      channel_id, wa_category, wa_tags
    """
    # base template for a single result
    def _base_result():
        return {
            'sender': None,
            'recipient': None,
            'text': None,
            'from_name': None,
            'chat_name': None,
            'received_at': None,
            'message_id': None,
            'quoted_id': None,
            'quoted_author': None,
            'quoted_text': None,
            'status': None,
            'from_me': False,
            'chat_id': None,
            'channel_id': None,
            'wa_category': None,
            'wa_tags': None,
        }

    try:
        # If payload is a list, process each element and return list
        if isinstance(payload, (list, tuple)):
            results = []
            for entry in payload:
                # If entry wraps messages, expand
                if isinstance(entry, dict) and isinstance(entry.get('messages'), (list, tuple)):
                    for m in entry.get('messages'):
                        info = extract_from_message_section(m)
                        # map recipient at wrapper level if present
                        if not info.get('recipient') and entry.get('to'):
                            info['recipient'] = normalize_phone(entry.get('to'))
                        # carry channel_id if set at wrapper
                        if entry.get('channel_id'):
                            info['channel_id'] = entry.get('channel_id')
                        results.append(info)
                else:
                    # try to extract as single message dict
                    if isinstance(entry, dict) and ('id' in entry or 'text' in entry or 'message_id' in entry or 'from' in entry):
                        info = extract_from_message_section(entry)
                        results.append(info)
                    else:
                        # unknown element type -> minimal mapping
                        r = _base_result()
                        r['text'] = str(entry)
                        results.append(r)
            return results

        # If payload is dict
        if isinstance(payload, dict):
            # expose channel id
            channel = payload.get('channel_id') or payload.get('channel')
            # if payload contains messages list -> return list of infos
            msgs = payload.get('messages') or payload.get('message') or None
            if isinstance(msgs, (list, tuple)) and len(msgs) > 0:
                results = []
                for m in msgs:
                    info = extract_from_message_section(m)
                    # pass through recipient at wrapper level if present
                    if not info.get('recipient'):
                        for k in ('to', 'recipient', 'toNumber', 'destination', 'owner'):
                            if payload.get(k):
                                info['recipient'] = normalize_phone(payload.get(k))
                                break
                    # attach channel id
                    if channel:
                        info['channel_id'] = channel
                    results.append(info)
                return results if len(results) > 1 else results[0]

            # fallback: try to parse single top-level message-like dict
            info = _base_result()
            info['channel_id'] = channel
            # message_id / text / sender mapping
            if payload.get('id') or payload.get('message_id'):
                extracted = extract_from_message_section(payload)
                info.update(extracted)
            else:
                # top-level shortcuts
                info['text'] = payload.get('text') or payload.get('body') or payload.get('message') or None
                # sender fallback
                for k in ('from', 'sender', 'phone', 'msisdn', 'wa_id'):
                    if payload.get(k):
                        info['sender'] = normalize_phone(payload.get(k))
                        break
                # recipient fallback
                for k in ('to', 'recipient', 'toNumber', 'destination', 'owner'):
                    if payload.get(k):
                        info['recipient'] = normalize_phone(payload.get(k))
                        break
                # timestamp
                ts = payload.get('timestamp') or payload.get('time') or payload.get('ts')
                info['received_at'] = _ts_to_odoo_string(ts)
                # attempt to extract tags from text
                cat, tags = _extract_tags_from_text(info['text'] or '')
                if cat:
                    info['wa_category'] = cat
                if tags:
                    info['wa_tags'] = tags

            return info

        # payload is scalar (string...) -> put into text
        r = _base_result()
        r['text'] = str(payload)
        cat, tags = _extract_tags_from_text(r['text'])
        if cat:
            r['wa_category'] = cat
        if tags:
            r['wa_tags'] = tags
        return r

    except Exception as e:
        _logger.exception("extract_whapi_payload error: %s", e)
        return _base_result()
