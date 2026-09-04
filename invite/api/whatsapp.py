# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

"""
WhatsApp Cloud API Integration

Sends messages and media attachments via Meta's WhatsApp Business Cloud API.

Requirements (set in Event Settings > WhatsApp Settings):
- whatsapp_provider: "Official WhatsApp API"
- whatsapp_api_key: Permanent access token from Meta
- whatsapp_phone_number_id: Phone Number ID from Meta dashboard
- whatsapp_business_number: Your business phone number (e.g. +255712345678)
- whatsapp_api_version: e.g. "v21.0"

For media messages (invitation cards):
1. Uploads the file to Meta's servers → gets a media_id
2. Sends the message with the media_id as an attachment
"""

import frappe
import requests
from frappe.utils import get_url


def get_whatsapp_config():
    """Get WhatsApp API configuration from Event Settings."""
    settings = frappe.get_single("Event Settings")
    return {
        "enabled": (
            getattr(settings, "whatsapp_provider", "") in ("Official WhatsApp API", "Meta API")
            and getattr(settings, "whatsapp_api_key", "")
            and getattr(settings, "whatsapp_phone_number_id", "")
        ),
        "api_key": getattr(settings, "whatsapp_api_key", ""),
        "phone_number_id": getattr(settings, "whatsapp_phone_number_id", ""),
        "business_number": getattr(settings, "whatsapp_business_number", ""),
        "api_version": getattr(settings, "whatsapp_api_version", "v21.0"),
    }


def send_text_message(to_number, message):
    """Send a plain text WhatsApp message via Cloud API."""
    config = get_whatsapp_config()
    if not config["enabled"]:
        frappe.log_error("WhatsApp API not configured", "WhatsApp Integration")
        return False

    url = f"https://graph.facebook.com/{config['api_version']}/{config['phone_number_id']}/messages"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number.replace("+", ""),  # Remove +, Meta expects just digits
        "type": "text",
        "text": {"body": message},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result.get("messages"):
            frappe.logger().info(f"WhatsApp text sent to {to_number}")
            return True
        return False
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"WhatsApp text send failed: {e}", "WhatsApp Integration")
        return False


def send_media_message(to_number, caption, file_path_or_url, media_type=None):
    """Send a media message (image/document) via WhatsApp Cloud API.

    Steps:
    1. Upload the file to Meta to get a media_id
    2. Send the message referencing that media_id

    Args:
        to_number: Recipient phone number (with country code)
        caption: Message caption for the media
        file_path_or_url: Path (relative /files/) or full URL to the file
        media_type: 'image' or 'document' (auto-detected from extension if None)
    """
    config = get_whatsapp_config()
    if not config["enabled"]:
        frappe.log_error("WhatsApp API not configured", "WhatsApp Integration")
        return False, "WhatsApp API not configured"

    # Guard: file_path_or_url must not be None
    if not file_path_or_url:
        frappe.log_error("No file provided for WhatsApp media message", "WhatsApp Integration")
        return False, "No file provided"

    # Resolve file path
    if file_path_or_url.startswith("http"):
        file_url = file_path_or_url
    elif file_path_or_url.startswith("/"):
        file_url = get_url(file_path_or_url)
    else:
        file_url = get_url(f"/{file_path_or_url}")

    # Auto-detect media type from file extension
    if not media_type:
        ext = file_path_or_url.split(".")[-1].lower() if "." in str(file_path_or_url) else ""
        media_type = "document" if ext in ("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx") else "image"

    # Step 1: Upload media to get media_id
    media_id = _upload_media(file_url, media_type, config)
    if not media_id:
        return False, "Failed to upload media to WhatsApp"

    # Step 2: Send message with media
    to_clean = to_number.replace("+", "")
    url = f"https://graph.facebook.com/{config['api_version']}/{config['phone_number_id']}/messages"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    if media_type == "image":
        media_payload = {"id": media_id, "caption": caption}
        payload = {
            "messaging_product": "whatsapp",
            "to": to_clean,
            "type": "image",
            "image": media_payload,
        }
    else:
        filename = file_path_or_url.split("/")[-1] if "/" in file_path_or_url else "document.pdf"
        media_payload = {"id": media_id, "filename": filename, "caption": caption}
        payload = {
            "messaging_product": "whatsapp",
            "to": to_clean,
            "type": "document",
            "document": media_payload,
        }

    response = None
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result.get("messages"):
            frappe.logger().info(
                f"WhatsApp media ({media_type}) sent to {to_number}"
            )
            return True, result["messages"][0].get("id", "sent")
        return False, "No message ID returned"
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        if response is not None:
            try:
                error_detail = response.json().get("error", {}).get("message", str(e))
            except Exception:
                pass
        frappe.log_error(f"WhatsApp media send failed: {error_detail}", "WhatsApp Integration")
        return False, error_detail


def _upload_media(file_path_or_url, media_type, config):
    """Upload a file to WhatsApp servers and return the media_id.

    Uses Frappe's file manager to resolve both public and private files.
    """
    from frappe.utils.file_manager import get_file

    # Determine MIME type
    if media_type == "image":
        mime_type = _guess_image_mime(file_path_or_url)
    else:
        mime_type = _guess_document_mime(file_path_or_url)

    url = f"https://graph.facebook.com/{config['api_version']}/{config['phone_number_id']}/media"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
    }
    data = {
        "messaging_product": "whatsapp",
    }

    try:
        # Use Frappe's file manager to get the file content
        # (returns [filename, content] in this frappe version)
        filename, file_content = get_file(file_path_or_url)
        if not filename:
            filename = file_path_or_url.split("/")[-1].split("?")[0] or f"media.{mime_type.split('/')[-1]}"

        files = {
            "file": (filename, file_content, mime_type),
        }

        upload_response = requests.post(url, headers=headers, data=data, files=files, timeout=60)
        upload_response.raise_for_status()
        result = upload_response.json()
        return result.get("id")
    except Exception as e:
        frappe.log_error(f"WhatsApp media upload failed: {file_path_or_url} - {e}", "WhatsApp Integration")
        return None


def _guess_image_mime(url):
    """Guess image MIME type from URL extension."""
    url = url or ""
    url_lower = url.lower()
    if ".png" in url_lower:
        return "image/png"
    elif ".gif" in url_lower:
        return "image/gif"
    elif ".webp" in url_lower:
        return "image/webp"
    else:
        return "image/jpeg"


def _guess_document_mime(url):
    """Guess document MIME type from URL extension."""
    url = url or ""
    url_lower = url.lower()
    if ".pdf" in url_lower:
        return "application/pdf"
    elif ".doc" in url_lower:
        return "application/msword"
    elif ".docx" in url_lower:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ".xls" in url_lower:
        return "application/vnd.ms-excel"
    elif ".xlsx" in url_lower:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif ".ppt" in url_lower:
        return "application/vnd.ms-powerpoint"
    elif ".pptx" in url_lower:
        return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    else:
        return "application/octet-stream"
