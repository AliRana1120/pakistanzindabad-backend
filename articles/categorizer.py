"""
Urdu News Categorizer
Uses TF-IDF + Cosine Similarity — understands full sentence context,
far more accurate than keyword matching.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Rich Urdu text profiles for each category
# The more text, the better the model understands context
CATEGORY_PROFILES = {
    "politics": """
        حکومت پارلیمنٹ قومی اسمبلی سینیٹ وزیراعظم وزیراعلیٰ صدر گورنر
        عمران خان شہباز شریف مریم نواز بلاول آصف زرداری نواز شریف
        فضل الرحمان سراج الحق چوہدری پرویز الٰہی آصف علی زرداری
        الیکشن انتخابات ووٹ سیاست جماعت تحریک انصاف مسلم لیگ پیپلز پارٹی
        اپوزیشن کابینہ وزارت احتجاج دھرنا جلسہ ریلی بیان گرفتاری ضمانت
        مقدمہ عدالت فیصلہ قانون بل آرڈیننس سیاسی رہنما لیڈر
        ضمنی الیکشن نشست حلقہ الیکشن کمیشن نگران حکومت
        سپریم کورٹ ہائی کورٹ جج چیف جسٹس آئین ترمیم
    """,
    "sports": """
        کرکٹ بیٹنگ باؤلنگ وکٹ رنز اوور ٹیسٹ ون ڈے ٹی ٹوئنٹی پی ایس ایل
        بابر اعظم شاہین آفریدی محمد رضوان فخر زمان یاسر شاہ نسیم شاہ
        فٹبال گول ورلڈ کپ فیفا کھلاڑی ٹیم میچ ٹورنامنٹ چیمپئن
        اولمپکس میڈل ٹرافی کپتان کوچ اسٹیڈیم ہاکی اسکواش باکسنگ
        کھیل مقابلہ جیت شکست سیریز اننگز سنچری ہاف سنچری
        ایشیا کپ چیمپئنز ٹرافی آئی سی سی ٹیسٹ رینکنگ
        ریسلنگ ایتھلیٹکس تیراکی ٹینس بیڈمنٹن
        پاکستان کرکٹ بورڈ پی سی بی
    """,
    "business": """
        روپیہ ڈالر شرح سود مہنگائی افراط زر جی ڈی پی بجٹ ٹیکس محصول
        اسٹاک مارکیٹ کے ایس ای حصص سرمایہ کاری بینک اسٹیٹ بینک مرکزی بینک
        آئی ایم ایف قرضہ برآمدات درآمدات تجارت کاروبار صنعت ادارہ
        تیل پٹرول گیس بجلی مہنگا سستا کسان زراعت فصل گندم چینی
        اقتصادی معاشی آمدنی منافع خسارہ تجارتی خسارہ کرنٹ اکاؤنٹ
        سی پیک سرمایہ کار کمپنی فیکٹری پیداوار برآمد
        زرمبادلہ ذخائر ادائیگیاں سود قرض واپسی
    """,
    "technology": """
        ٹیکنالوجی سوشل میڈیا انٹرنیٹ موبائل اسمارٹ فون ایپ سافٹ ویئر
        ہیکنگ سائبر ڈیجیٹل آرٹیفیشل انٹیلیجنس اے آئی روبوٹ مشین لرننگ
        یوٹیوب فیس بک ٹویٹر ایکس واٹس ایپ ٹک ٹاک انسٹاگرام
        پی ٹی اے بلاک فائیو جی سیٹلائٹ کمپیوٹر لیپ ٹاپ گیمنگ ای کامرس
        جدید اختراع ایجاد ڈیوائس اسکرین پروسیسر چپ سیمی کنڈکٹر
        اسپیس ایکس اسٹار لنک سٹار شپ ناسا خلاء
        گوگل ایپل مائیکروسافٹ سیمسنگ ہواوے
        آن لائن ویب سائٹ ڈیٹا پرائیویسی سیکیورٹی
    """,
    "international": """
        امریکہ بھارت چین روس ایران افغانستان سعودی عرب ترکیہ
        اسرائیل فلسطین برطانیہ یورپ مشرق وسطیٰ خلیج دبئی
        اقوام متحدہ ناٹو او آئی سی شنگھائی تعاون تنظیم
        جنگ حملہ بمباری ڈرون فوجی آپریشن فائرنگ
        دہشت گردی القاعدہ داعش طالبان
        سفارتی سفیر دورہ معاہدہ بین الاقوامی تعلقات
        غزہ لبنان یوکرین روس یورپ عالمی بحران
        مودی بائیڈن پوتن اردوان نیتن یاہو
        ویزا تارکین وطن پناہ گزین
    """,
    "pakistan": """
        کراچی لاہور اسلام آباد پشاور کوئٹہ راولپنڈی ملتان فیصل آباد
        سیلاب زلزلہ حادثہ آگ دھماکہ پولیس رینجرز فوج آئی ایس آئی
        آپریشن گرفتار ملزم قتل تشدد صحت ہسپتال ڈاکٹر مریض
        تعلیم اسکول یونیورسٹی طالب علم استاد
        بارش موسم گرمی سردی طوفان خشک سالی
        پاکستانی شہری عوام ملک قومی صوبہ ضلع
        ٹریفک حادثہ سڑک موٹر وے
        بجلی لوڈ شیڈنگ پانی گیس
    """,
}

CATEGORY_NAMES = list(CATEGORY_PROFILES.keys())
CATEGORY_TEXTS = [CATEGORY_PROFILES[c] for c in CATEGORY_NAMES]

# Build the model once at startup
_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
_category_vectors = _vectorizer.fit_transform(CATEGORY_TEXTS)


def categorize(title: str, description: str = "", feed_category: str = "all") -> str:
    """
    Returns the best matching category slug using TF-IDF cosine similarity.
    Falls back to feed_category if confidence is too low.
    """
    text = f"{title} {description}".strip()
    if not text:
        return feed_category if feed_category != "all" else "pakistan"

    try:
        vec = _vectorizer.transform([text])
        similarities = cosine_similarity(vec, _category_vectors)[0]
        best_idx = int(np.argmax(similarities))
        best_score = similarities[best_idx]

        # Low confidence — trust the feed's own category
        if best_score < 0.05:
            return feed_category if feed_category != "all" else "pakistan"

        # If score difference between top two is tiny, trust feed category
        sorted_scores = sorted(similarities, reverse=True)
        if len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1]) < 0.02:
            if feed_category != "all":
                return feed_category

        return CATEGORY_NAMES[best_idx]
    except Exception:
        return feed_category if feed_category != "all" else "pakistan"