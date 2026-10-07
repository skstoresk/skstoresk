"""Gmail order emails (SMTP + App Password from secrets)."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from . import config
from .utils import format_price


def _send(to_email: str, subject: str, html_body: str):
    """Returns (ok, message). Never raises."""
    if not to_email:
        return False, "no recipient"
    if not config.email_configured():
        return False, "Gmail not configured in secrets"
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{config.STORE_NAME} <{config.GMAIL_USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=25) as s:
            s.starttls()
            s.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            s.send_message(msg)
        return True, "sent"
    except Exception as e:  # noqa: BLE001 - report, don't crash checkout
        return False, str(e)


def _items_table(order) -> str:
    rows = ""
    for it in order.get("items", []) or []:
        rows += (
            f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{it.get('name','')}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:center'>{it.get('qty',1)}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:right'>"
            f"{format_price(it.get('price',0))}</td></tr>"
        )
    return (
        "<table style='width:100%;border-collapse:collapse'>"
        "<tr><th style='text-align:left;padding:8px'>Item</th>"
        "<th style='padding:8px'>Qty</th>"
        "<th style='text-align:right;padding:8px'>Price</th></tr>"
        f"{rows}</table>"
    )


def _shell(title: str, body: str) -> str:
    return (
        "<div style='font-family:Arial,sans-serif;max-width:600px;margin:auto;"
        "border:1px solid #eee;border-radius:12px;overflow:hidden'>"
        "<div style='background:#0f0f14;color:#f5c451;padding:20px;text-align:center'>"
        f"<h2 style='margin:0'>{config.STORE_NAME} 🛍️</h2></div>"
        f"<div style='padding:24px;color:#222'><h3 style='margin-top:0'>{title}</h3>{body}</div>"
        "<div style='padding:16px;text-align:center;color:#888;font-size:12px'>"
        "Made with ❤ &nbsp;|&nbsp; © Kaleem</div></div>"
    )


def send_customer_confirmation(order: dict):
    if not order.get("customer_email"):
        return False, "customer has no email"
    body = (
        f"<p>Assalam-o-Alaikum <b>{order['customer_name']}</b>,</p>"
        "<p>Thank you for shopping with us! Your order has been received. "
        "Payment will be collected as <b>Cash on Delivery</b>.</p>"
        f"<p><b>Order number:</b> {order['order_number']}</p>"
        f"{_items_table(order)}"
        f"<p><b>Delivery fee:</b> {format_price(order.get('delivery_fee', 0))}<br>"
        f"<b>Total (COD):</b> {format_price(order.get('total', 0))}</p>"
        "<p>You can track your order anytime from our website's "
        "<b>Track Order</b> page using your order number.</p>"
    )
    return _send(
        order["customer_email"],
        f"Order confirmed — {order['order_number']} | {config.STORE_NAME}",
        _shell("✅ Order Confirmed", body),
    )


def send_admin_alert(order: dict):
    if not config.ADMIN_NOTIFY_EMAIL:
        return False, "admin email not configured"
    body = (
        "<p><b>New order received!</b></p>"
        f"<p><b>Order:</b> {order['order_number']}<br>"
        f"<b>Customer:</b> {order['customer_name']} ({order['phone']})<br>"
        f"<b>Address:</b> {order['address']}, {order['city']}, {order['country']}<br>"
        f"<b>Total (COD):</b> {format_price(order.get('total', 0))}</p>"
        f"{_items_table(order)}"
        "<p>Open the admin portal → Orders to confirm &amp; ship.</p>"
    )
    return _send(
        config.ADMIN_NOTIFY_EMAIL,
        f"🛒 New order {order['order_number']} — {format_price(order.get('total', 0))}",
        _shell("New Order Alert", body),
    )


def send_status_update(order: dict):
    if not order.get("customer_email"):
        return False, "customer has no email"
    tracking = order.get("tracking_id")
    body = (
        f"<p>Assalam-o-Alaikum <b>{order['customer_name']}</b>,</p>"
        f"<p>Your order <b>{order['order_number']}</b> status is now: "
        f"<b>{order['status']}</b>.</p>"
    )
    if tracking:
        body += f"<p><b>Tracking ID:</b> {tracking}</p>"
    body += "<p>Thank you for shopping with " + config.STORE_NAME + "!</p>"
    return _send(
        order["customer_email"],
        f"Order {order['order_number']} — {order['status']} | {config.STORE_NAME}",
        _shell("📦 Order Update", body),
    )
