"""Persian user-facing strings and enum/pillar label maps."""

from __future__ import annotations

from collections.abc import Mapping

CONTENT_TYPE_LABELS = {
    "open_source_analysis": "تحلیل اپن‌سورس",
    "tool_experiment": "آزمایش ابزار و تکنیک",
    "personal_project": "نمایش پروژه شخصی",
    "educational_post": "پست آموزشی",
    "short_video": "ویدیوی کوتاه",
}

CONTENT_STATUS_LABELS = {
    "idea": "ایده",
    "researching": "در حال تحقیق",
    "drafting": "در حال نگارش",
    "review": "بازبینی",
    "scheduled": "زمان‌بندی‌شده",
    "published": "منتشرشده",
    "archived": "بایگانی‌شده",
}

IDEA_STATUS_LABELS = {
    "inbox": "صندوق ورودی",
    "shortlisted": "انتخاب اولیه",
    "selected": "انتخاب‌شده",
    "rejected": "ردشده",
}

PILLAR_LABELS = {
    "open_source_deep_dive": "تحلیل اپن‌سورس",
    "tool_experiment": "آزمایش ابزار",
    "personal_project": "پروژه شخصی",
    "educational_post": "پست آموزشی",
}

EFFORT_LABELS = {"low": "کم", "medium": "متوسط", "high": "زیاد"}

CONTACT_STAGE_LABELS = {
    "identified": "شناسایی‌شده",
    "connection_planned": "در انتظار اتصال",
    "connected": "متصل‌شده",
    "conversation_started": "گفتگو شروع‌شده",
    "qualified_lead": "لید واجد شرایط",
    "proposal": "پروپوزال",
    "won": "برنده",
    "lost": "ازدست‌رفته",
}

OPPORTUNITY_STATUS_LABELS = {
    "none": "—",
    "exploring": "در حال بررسی",
    "proposal_sent": "پروپوزال ارسال‌شده",
    "negotiating": "در حال مذاکره",
    "won": "برنده",
    "lost": "ازدست‌رفته",
}

METRIC_LABELS = {
    "impressions": "بازدید",
    "reactions": "واکنش",
    "comments": "کامنت",
    "reposts": "بازنشر",
    "profile_views": "بازدید پروفایل",
    "connection_requests": "درخواست اتصال",
    "qualified_conversations": "گفتگوی واجد شرایط",
    "leads": "لید",
}

CRITERION_LABELS = {
    "audience_relevance": "مرتبط بودن با مخاطب",
    "demonstrability": "قابلیت نمایش",
    "technical_depth": "عمق فنی",
    "business_relevance": "ارزش کسب‌وکاری",
    "effort_required": "زحمت لازم",
}

EDIT_FIELD_LABELS = {
    "title": "عنوان",
    "topic": "موضوع",
    "hook": "هوک (شروع)",
    "outline": "رئوس مطالب",
    "draft": "پیش‌نویس",
    "call_to_action": "فراخوان اقدام (CTA)",
    "notes": "یادداشت",
    "reference_url": "لینک مرجع",
}


def label(mapping: Mapping[str, str], key: str | None) -> str:
    if key is None:
        return "—"
    return mapping.get(key, key)


# --- Messages ---

MSG_START = (
    "سلام {name} 👋\n\n"
    "به «لینکدین گروث اوس» خوش اومدی.\n"
    "اینجا می‌تونی محتوای فنی رو برنامه‌ریزی و منتشر کنی، ایده‌ها رو مدیریت کنی، "
    "تسک‌های روزانه رو دنبال کنی و نتایج رو بسنجی.\n\n"
    "از منوی زیر شروع کن 👇"
)

MSG_HELP = (
    "دستورها:\n"
    "/today — تسک‌های امروز\n"
    "/week — برنامه هفته\n"
    "/ideas — مدیریت ایده‌ها\n"
    "/content — مدیریت محتوا\n"
    "/stats — آمار\n"
    "/leads — لیدها و شبکه‌سازی\n"
    "/settings — تنظیمات\n"
    "/cancel — لغو عملیات جاری"
)

MSG_CANCEL = "عملیات جاری لغو شد."

MSG_COMING_SOON = "این بخش در نسخه بعدی کامل می‌شود."
