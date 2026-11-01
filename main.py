from __future__ import annotations

import os
import random
from itertools import product
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="mr.typing", docs_url=None, redoc_url=None)

# The content pools are deterministic and finite: no retry-until-unique loops.
# Each pool is built from curated phrase parts, then checked at startup.
AR_EASY_OPENERS = [
    "في صباح هادئ", "بعد استراحة قصيرة", "في نهاية الأسبوع", "مع بداية يوم جديد",
    "قبل غروب الشمس", "في مكتبة الحي", "خلال رحلة ممتعة", "بعد انتهاء الدرس",
    "في مساء لطيف", "عند أول ضوء", "في طريق العودة", "خلال وقت الفراغ",
    "قبل بدء العمل", "في يوم مشمس", "بعد قراءة مفيدة", "في ساحة المدرسة",
    "خلال لقاء الأصدقاء", "مع نسمة الصباح", "في عطلة جميلة", "بعد ترتيب المكتب",
]
AR_EASY_ENDINGS = [
    "بدأ الطالب يومه بخطة واضحة", "اختار المتدرب هدفاً صغيراً", "قرأ الطفل قصة ممتعة",
    "كتب الكاتب فكرة جديدة", "رتبت سارة مكتبها بعناية", "تعلم الفريق مهارة نافعة",
    "زرع الجيران شتلة صغيرة", "رسم الفنان لوحة جميلة", "ساعد الصديق زميله بسرور",
    "أنجزت المعلمة عملاً متقناً", "وجد المسافر طريقاً آمناً", "راجع القارئ ملاحظاته بهدوء",
    "صنع الحرفي قطعة أنيقة", "فتح الطالب نافذة الغرفة", "حفظت ليلى أبياتاً قصيرة",
    "استمع الجميع إلى حكاية لطيفة", "شارك اللاعب في تدريب ممتع", "اختارت الأسرة نزهة قريبة",
    "أضاء المصباح زاوية المكان", "أنهى المتعلم تمرينه بثقة",
]
EN_EASY_OPENERS = [
    "On a quiet morning", "After a short break", "At the weekend", "At the start of a new day",
    "Before sunset", "At the neighborhood library", "During a pleasant trip", "After class",
    "On a lovely evening", "At first light", "On the way home", "In some free time",
    "Before work began", "On a sunny day", "After a helpful read", "In the school yard",
    "During a friendly visit", "With the morning breeze", "On a nice holiday", "After tidying the desk",
]
EN_EASY_ENDINGS = [
    "the student began the day with a clear plan", "the learner chose a small goal", "the child read a fun story",
    "the writer noted a new idea", "Sara arranged her desk with care", "the team learned a useful skill",
    "the neighbors planted a small tree", "the artist painted a lovely picture", "the friend gladly helped a classmate",
    "the teacher finished careful work", "the traveler found a safe path", "the reader reviewed notes calmly",
    "the craft worker made a neat piece", "the student opened the room window", "Layla learned a short poem",
    "everyone listened to a kind story", "the player joined a fun practice", "the family chose a nearby walk",
    "the lamp lit a quiet corner", "the learner finished the exercise with confidence",
]

AR_MID_OPENERS = [
    "مع إشراقة يوم جديد", "في مركز الحي", "بعد نقاش هادئ", "خلال مشروع تعاوني",
    "في طريق مليء بالأشجار", "بعد مراجعة الخطة", "في ورشة صغيرة", "مع اقتراب المساء",
    "خلال أسبوع حافل", "في رحلة إلى الساحل",
]
AR_MID_ACTIONS = [
    "جمع الفريق أفكاره ورتب أولوياته", "راجع الطالب مصادره وتحقق من التفاصيل",
    "أعدت المصممة نموذجاً واختبرت ألوانه", "نظم المتطوعون المكان واستقبلوا الزوار",
    "كتب الباحث ملاحظاته وقارن النتائج", "تدرب اللاعب على مهاراته وطور أداءه",
    "رتبت الأسرة احتياجاتها واختارت وجهتها", "زرع الأطفال شتلات جديدة وسقوها بعناية",
    "تبادل الأصدقاء الخبرات واقترحوا حلولاً", "أصلح الفني الجهاز وفحص مكوناته",
]
AR_MID_ENDINGS = [
    "ثم عرضوا العمل على الجميع", "ثم سجلوا ما تعلموه في دفتر", "ثم احتفلوا بتحقيق هدفهم",
    "ثم واصلوا الطريق بخطوات واثقة",
]
EN_MID_OPENERS = [
    "At the start of a new day", "At the community center", "After a calm discussion", "During a team project",
    "Along a tree-lined path", "After reviewing the plan", "In a small workshop", "As evening drew near",
    "During a busy week", "On a trip to the coast",
]
EN_MID_ACTIONS = [
    "the team gathered ideas and set priorities", "the student checked sources and reviewed details",
    "the designer made a draft and tested its colors", "the volunteers arranged the place and welcomed guests",
    "the researcher wrote notes and compared results", "the player practiced skills and improved performance",
    "the family listed its needs and chose a destination", "the children planted seedlings and watered them carefully",
    "the friends shared experience and suggested solutions", "the technician fixed the device and checked its parts",
]
EN_MID_ENDINGS = [
    "then they showed the work to everyone", "then they wrote what they learned in a notebook",
    "then they celebrated reaching their goal", "then they continued with confidence",
]

AR_HARD_OPENERS = [
    "بعد أسابيع من التخطيط", "في صباح ازدحمت فيه الشوارع", "مع انطلاق المبادرة الجديدة",
    "في قرية تحيط بها الجبال", "بعد أن انتهى الفريق من التجربة", "عندما اجتمع الخبراء في المركز",
    "في مساء حمل أخباراً مفرحة", "بعد رحلة طويلة بين المدن", "مع بداية الفصل الدراسي",
    "في محطة صغيرة قرب البحر",
]
AR_HARD_ACTIONS = [
    "راجع المشاركون البيانات بدقة وقارنوا النتائج", "تعاون المهندسون على بناء نموذج أكثر كفاءة",
    "جمع الطلاب مصادر متعددة وناقشوا الأفكار", "أعدت المجموعة خطة مرنة تراعي احتياجات الجميع",
    "وثق الباحث ملاحظاته وشرح أسباب التغيير", "اختبر الفريق الأدوات وحدد مواضع التحسين",
    "نظمت المتطوعات ورشاً قصيرة لتبادل المعرفة", "حلل المصممون ملاحظات المستخدمين ورتبوا الأولويات",
    "أكمل الحرفيون العمل وأتقنوا أدق التفاصيل", "نسق المنظمون البرنامج وفتحوا المجال للمشاركة",
]
AR_HARD_ENDINGS = [
    "وبذلك أصبح المشروع أقرب إلى تحقيق أثره المستدام", "مما منح المجتمع فرصة أوسع للتعلم والتعاون",
    "لتتحول الفكرة إلى تجربة ناجحة قابلة للتطوير", "ثم شاركوا خلاصتهم ليستفيد منها الآخرون",
]
EN_HARD_OPENERS = [
    "After weeks of careful planning", "On a morning of busy streets", "As the new initiative began",
    "In a village surrounded by mountains", "After the team finished its trial", "When experts met at the center",
    "On an evening with joyful news", "After a long journey between cities", "At the start of the school term",
    "At a small station near the sea",
]
EN_HARD_ACTIONS = [
    "the participants checked data and compared results", "the engineers worked together on a more efficient model",
    "the students gathered sources and discussed ideas", "the group prepared a flexible plan for everyone's needs",
    "the researcher documented notes and explained the change", "the team tested tools and found areas to improve",
    "the volunteers hosted short sessions to share knowledge", "the designers reviewed feedback and set priorities",
    "the craft workers finished the task with careful detail", "the organizers planned the program and invited everyone",
]
EN_HARD_ENDINGS = [
    "and the project moved closer to lasting impact", "which gave the community more room to learn together",
    "turning the idea into a successful and useful experience", "then they shared their findings for others to use",
]

AR_PLACES = ["مدينة هادئة", "قرية بعيدة", "جزيرة صغيرة", "حي قديم", "غابة واسعة", "ميناء جميل", "مدرسة قريبة", "سوق مزدحم", "واد أخضر", "محطة قطار"]
AR_CHARACTERS = ["كاتب شاب", "مسافرة فضولية", "طفل شجاع", "عالمة حكيمة", "فنان موهوب", "معلمة محبة", "مخترع صغير", "بحار هادئ", "طبيبة مجتهدة", "موسيقي غامض"]
AR_GOALS = ["اكتشاف مكان جديد", "تعلم لغة مختلفة", "إنقاذ حديقة جميلة", "كتابة قصة ملهمة", "بناء آلة ذكية", "مساعدة صديق قديم", "رسم خريطة غامضة", "إقامة مهرجان كبير", "حل لغز صعب", "بدء مشروع مفيد"]
AR_STORY_ENDINGS = ["اجتمع الأصدقاء للمساعدة", "وصلت رسالة تحمل خبراً سعيداً", "وجدوا خريطة تقود إلى الحل", "تعلم الجميع درساً مهماً", "عاد الفريق بفكرة أكثر إشراقاً"]
EN_PLACES = ["a quiet city", "a distant village", "a small island", "an old neighborhood", "a wide forest", "a lovely harbor", "a nearby school", "a busy market", "a green valley", "a train station"]
EN_CHARACTERS = ["a young writer", "a curious traveler", "a brave child", "a wise scientist", "a talented artist", "a caring teacher", "a young inventor", "a calm sailor", "a dedicated doctor", "a mysterious musician"]
EN_GOALS = ["discovering a new place", "learning a different language", "saving a lovely garden", "writing an inspiring story", "building a clever machine", "helping an old friend", "drawing a hidden map", "hosting a grand festival", "solving a difficult puzzle", "starting a useful project"]
EN_STORY_ENDINGS = ["friends gathered to help", "a letter arrived with joyful news", "they found a map that led to the answer", "everyone learned an important lesson", "the team returned with a brighter idea"]

AR_NEWS_PLACES = ["المدينة", "الجامعة", "المركز الثقافي", "الحي الجديد", "الواجهة البحرية", "المدرسة", "المكتبة العامة", "القرية", "الحديقة", "المحطة"]
AR_NEWS_EVENTS = ["افتتاح مركز ثقافي جديد", "إطلاق مبادرة للقراءة", "تطوير خدمة النقل", "تنظيم مهرجان محلي", "إنشاء مساحة خضراء", "عرض مشروع طلابي", "بدء برنامج تدريبي", "تدشين معرض فني", "توسعة مرفق عام", "إعلان نتائج بحثية"]
AR_NEWS_REACTIONS = ["مشاركة واسعة من الأهالي", "إقبال لافت من الزوار", "تعاون جهات محلية متعددة", "اهتمام كبير من الشباب"]
AR_NEWS_GOALS = ["دعم التعلم", "تحسين جودة الحياة", "تعزيز المشاركة المجتمعية", "إتاحة فرص جديدة"]
EN_NEWS_PLACES = ["the city", "the university", "the arts center", "the new district", "the waterfront", "the school", "the public library", "the village", "the garden", "the station"]
EN_NEWS_EVENTS = ["a new arts center opening", "a reading program launching", "transport service improving", "a local festival taking place", "a green space being created", "a student project being shown", "a training program beginning", "an art exhibit opening", "a public facility expanding", "research findings being announced"]
EN_NEWS_REACTIONS = ["strong local participation", "a notable visitor turnout", "cooperation between local groups", "wide interest from young people"]
EN_NEWS_GOALS = ["support learning", "improve quality of life", "strengthen community ties", "create new opportunities"]

# 350 distinct Arabic practice tokens are built from 70 common words and five
# valid written forms (bare, definite, and common attached clitics).
AR_WORD_BASE = """
بيت كتاب شمس قمر طريق نافذة حديقة مدرسة قلم مدينة بحر سيارة زهرة طاولة هاتف حاسوب وقت حلم نجاح صديق ماء شجرة باب غرفة طعام سفر مطر سحابة جبل نهر نجمة صباح مساء عائلة موسيقى فكرة لعبة عمل ذاكرة لغة صوت لون قصة دفتر حقيبة مفتاح كرسي ساعة خبز تفاح قهوة وردة طائر سمكة طفل معلم طبيب سوق قرية قطار طائرة سفينة طاقة رياضة صحة مهارة علم فن صبر أمل فرح سلام ضوء حجر رمل ثلج نار هواء وطن رسالة صورة شاشة لوحة حرف سرعة دقة تدريب هدف عادة اختيار ابتكار تعاون معرفة راحة مطبخ حذاء ثوب مركز مسرح حفل كتابات هاتفية مكتبة مزرعة ملعب مطار مطعم فندق شارع جسر نفق محطة شاطئ صحراء واحة واد سهل غيمة برق رعد ربيع صيف خريف شتاء عصفور حصان جمل أرنب أسد نمر غزال ذئب فيل دب فراشة نحلة نملة سماء أرض بحرية موج رصيف سفينة ميناء بستان نخلة زيتون عنب ليمون موز برتقال خوخ تمر حليب جبن أرز خبز لحم دجاج بيضة ملح سكر عسل تمرين مباراة فريق لاعب ملعب كرة سباق رحلة عطلة عمل دراسة جامعة معهد فصل درس واجب مشروع تجربة بحث مختبر مهندس مبرمج مصمم فنان شاعر كاتب قارئ متعلم مدرب مرشد قائد زميل جار أخ أخت أب أم جد جدة عم خال ابن بنت صبي فتاة رجل امرأة ضيف زائر حارس بائع سائق طيار بحار مزارع راع ممرض ممرضة معلمة مدير عامل موظف حرفي نجار حداد خياط طباخ مصور ممثل مخرج صحفي محرر طبيعة بيئة طاقة شمسية هواء نقي تربة بذرة غصن ورقة جذر ثمر لون أبيض أسود أزرق أخضر أحمر أصفر وردي بنفسجي بني رمادي جميل هادئ سريع واضح قوي لطيف عميق واسع قريب بعيد جديد قديم صغير كبير قصير طويل نظيف مرتب صعب سهل ذكي نشيط صادق كريم شجاع لطيف مفيد رائع متين مريح متوازن آمن مفاجأة خبر سؤال جواب حكاية نص صفحة كتاب مجلة جريدة فقرة عنوان خبر صحيفة قصة مقالة رسالة دعوة بطاقة بريد صندوق مفتاح قفل نافذة ستارة مصباح كرسي أريكة سجادة مرآة ساعة تقويم ورقة ملصق صورة كاميرا عدسة شاشة لوحة مفتاح فأرة جهاز شبكة تطبيق موقع ملف مجلد رابط كلمة جملة فقرة لغة ترجمة لهجة محادثة صوت تسجيل أغنية نغمة لحن إيقاع آلة عود بيانو كمان طبل ريشة مسرح منصة جمهور جمهور تذكرة رحلة حافلة سيارة دراجة شاحنة قطار سكة سفينة زورق طائرة جناح مطار حقيبة جواز خريطة طريق اتجاه شمال جنوب شرق غرب نقطة مسافة سرعة خطوة بداية نهاية مرحلة خطة موعد يوم أسبوع شهر سنة دقيقة ثانية ساعة صباح مساء ظهر فجر ليل نهار أمس اليوم غدا قريباً دائماً أحياناً كثيراً قليلاً الآن لاحقاً هنا هناك فوق تحت أمام خلف يمين يسار داخل خارج قرب بعيد بين حول مع ضد إلى من عن على في عند نحو بسبب خلال قبل بعد حتى منذ ثم أو لكن لأن لذلك عندما حيث بينما ربما غالباً أبداً نعم لا شكراً أهلاً مرحباً سلام وداعاً من فضلك تفضل آسف عذراً ممتاز رائع جميل أحسنت نجاح تقدم إنجاز هدف مهارة معرفة حكمة فكرة رأي قرار فرصة تجربة تدريب ممارسة تعلم تعليم كتابة قراءة حفظ فهم تركيز انتباه ذاكرة تفكير تخطيط ترتيب تنظيم مشاركة تعاون مساعدة احترام صداقة محبة فرح سعادة أمان راحة ثقة أمل صبر هدوء قوة نشاط صحة حركة نوم طعام شراب فطور غداء عشاء وجبة خبز لبن عصير ماء شاي قهوة شوربة سلطة فاكهة خضار بطاطس طماطم خيار جزر بصل ثوم نعناع ريحان زعتر قرفة فلفل زيت زبدة دقيق حلوى كعكة بسكويت شوكولاتة وجبة مطعم طاولة صحن كوب ملعقة شوكة سكين قدر فرن ثلاجة غسالة مكنسة صابون منشفة مرآب حديقة منزل شقة غرفة صالة حمام مكتب متجر محل سوق بنك مستشفى عيادة صيدلية مدرسة جامعة مسجد كنيسة متحف معرض ملعب نادي حديقة بحر جبل نهر غابة مزرعة حقل بيت مدينة قرية عاصمة دولة قارة جزيرة كوكب فضاء نجم شمس قمر سحاب مطر ثلج ريح عاصفة طقس حرارة برودة فصل موسم شروق غروب ظل نور ضوء لون شكل دائرة مربع مثلث خط نقطة سطح زاوية حجم وزن طول عرض ارتفاع عمق مساحة حجم مادة خشب معدن حديد ذهب فضة زجاج ورق قماش جلد بلاستيك حجر طين رمل ملح ماء نار دخان بخار كهرباء بطارية شاحن سلك زر مفتاح قفل باب درج خزانة رف صندوق حقيبة محفظة نقود عملة بطاقة تذكرة فاتورة سعر متجر بائع مشتري زبون خدمة طلب توصيل طرد صندوق رسالة بريد عنوان هاتف رقم رمز كلمة مرور حساب دخول خروج تسجيل حفظ حذف تعديل تحديث بحث اختيار قائمة صفحة نافذة رابط زر نموذج حقل صورة شعار رمز لون تصميم شكل تجربة مستخدم واجهة نظام برنامج تطبيق موقع خادم قاعدة بيانات ملف نسخة نسخة احتياطية أمان خصوصية سرعة جودة أداء خطأ إصلاح حل مشكلة مساعدة دعم تحديث إصدار إعداد خيار تفضيل إشعار تنبيه رسالة بريد حساب تطبيق برنامج شبكة إنترنت اتصال اتصال لاسلكي جهاز حاسوب لوحة مفاتيح فأرة سماعة ميكروفون كاميرا هاتف ذكي جهاز لوحي حاسوب محمول شاشة طابعة ماسح ضوئي قلم حبر رصاص ممحاة مسطرة دفتر ورقة ملف كتاب قصة جريدة مجلة صحيفة مقالة قصيدة بيت شعر لغة عربية إنجليزية كلمة اسم فعل حرف صوت مقطع معنى مرادف تضاد جمع مفرد جذر وزن صرف نحو إملاء قراءة كتابة خط نسخ رقعة كاتب قارئ طالب معلم درس فصل مدرسة مكتبة جامعة دورة تدريب اختبار نتيجة درجة علامة سؤال جواب شرح مثال تمرين واجب مشروع بحث مقال تقرير عرض تقديمي اجتماع نقاش حوار فكرة هدف خطة جدول قائمة مهمة موعد وقت إنجاز خطوة تقدم تأخير بداية نهاية مرحلة فرصة نجاح فشل محاولة صبر تركيز دقة سرعة مهارة خبرة عادة معرفة علم تقنية هندسة برمجة تصميم رسم تصوير موسيقى رياضة صحة طعام سفر سياحة ثقافة فن تاريخ جغرافيا طبيعة مجتمع أسرة صديق جار زميل فريق مجموعة شركة مؤسسة جمعية مدينة حي طريق مكان موقع متجر منزل مساحة خدمة مركز برنامج مشروع نشاط مسابقة جائزة ميدالية كأس بطولة مباراة فريق لاعب مدرب حكم جمهور ملعب كرة سلة طائرة قدم يد سباحة ركض مشي قفز دراجة يوجا لياقة تمرين عضلة نفس طاقة حركة هدف فوز خسارة تعادل نتيجة جولة منافس تدريب مهارة سرعة دقة تعاون احترام شرف شجاعة أمانة وفاء كرم لطف تواضع عدل نظام قانون حق واجب مسؤولية قرار اختيار نصيحة تجربة قصة حكاية ذكرى حلم أمنية فرح حزن غضب خوف دهشة مفاجأة ابتسامة ضحكة دمعة صوت همس نداء سؤال جواب نقاش فكرة رأي حجة دليل برهان حقيقة معلومة خبر إشاعة مصدر مرجع بحث معرفة حكمة علم تجربة اكتشاف اختراع ابتكار تطوير تحسين تغيير نمو تقدم مستقبل حاضر ماض يوم غد أمس أسبوع شهر عام سنة وقت لحظة ثانية دقيقة ساعة صباح مساء ظهر عصر مغرب عشاء فجر ليل نهار فصل ربيع صيف خريف شتاء موسم طقس مناخ سحاب غيم مطر رذاذ ثلج برد حر نسيم هواء ريح عاصفة برق رعد ضباب شمس ضوء ظل قمر هلال بدر نجم كوكب فضاء سماء أرض بحر محيط نهر واد بحيرة شلال عين ينبوع بئر جزيرة ساحل شاطئ رمل صخر جبل تل هضبة وادي سهل غابة شجر غصن ورق زهرة وردة عشب نبات بذرة ثمرة فاكهة خضار مزرعة حقل حديقة بستان نخلة زيتونة تفاحة موزة برتقالة ليمونة فراولة عنبة خوخة مشمشة رمانة بطيخة شمامة طماطم خيار جزر بطاطس بصل ثوم فلفل خس سبانخ نعناع ريحان بقدونس كزبرة شبت قرفة هيل زنجبيل كركم كمون ملح سكر عسل تمر حليب لبن جبن زبدة قشطة لبنة خبز أرز قمح شعير ذرة شوفان دقيق عجين معكرونة شوربة مرق لحم دجاج سمك تونة بيض بيضة زيت زيتون ماء عصير شاي قهوة كاكاو شوكولاتة حلوى كعكة بسكويت فطيرة بيتزا سلطة وجبة طبق صحن كوب فنجان كأس ملعقة شوكة سكين قدر مقلاة فرن موقد ثلاجة خزانة مطبخ مطعم مقهى مخبز متجر سوق بائع طباخ شيف نادل زبون طلب قائمة فاتورة سعر نقود محفظة بطاقة بنك حساب عملة ريال درهم دولار متجر مركز خدمة هاتف جوال حاسوب كمبيوتر شاشة لوحة مفاتيح فأرة سماعة كاميرا ميكروفون طابعة ماسح شاحن بطارية سلك مقبس مصباح ضوء مروحة مكيف جهاز ساعة منبه تقويم دفتر قلم رصاص حبر ممحاة مسطرة حقيبة محفظة مفتاح قفل باب نافذة جدار سقف أرضية غرفة منزل شقة بيت فيلا قصر مبنى برج مدرسة جامعة مكتب متجر مصنع مستشفى عيادة صيدلية مركز مسجد حديقة متحف مسرح سينما ملعب محطة مطار ميناء فندق شاطئ شارع طريق جسر نفق ساحة حارة حي قرية مدينة عاصمة دولة وطن عالم قارة منطقة مكان مسافة اتجاه خريطة موقع عنوان رقم رمز بريد رسالة ظرف صندوق طرد حقيبة سفر جواز تذكرة رحلة طائرة قطار حافلة سيارة دراجة شاحنة سفينة زورق مركب سفينة رصيف سكة محطة موقف إشارة طريق شارع زقاق ممر درج سلم مصعد باب مدخل مخرج جهة شمال جنوب شرق غرب يمين يسار أمام خلف أعلى أسفل وسط طرف جانب قرب بعد داخل خارج حول فوق تحت بين مع دون إلى من عن على في عند لدى نحو حتى منذ قبل بعد خلال أثناء تجاه بسبب بواسطة مثل غير نفس كل بعض أكثر أقل كثير قليل واسع ضيق طويل قصير عريض رفيع عميق سطحي ثقيل خفيف سريع بطيء سهل صعب بسيط معقد واضح غامض جميل قبيح جديد قديم حديث تقليدي عصري ذكي مفيد رائع ممتاز جيد أفضل أحسن كامل ناقص صحيح خطأ آمن نظيف مرتب هادئ نشيط قوي لطيف كريم شجاع صادق أمين عادل حكيم مرح محبوب سعيد حزين غاضب خائف متفاجئ متعب نشيط جاهز مشغول فارغ ممتلئ مفتوح مغلق دافئ بارد حار رطب جاف ناعم خشن حلو مالح مر حامض طازج لذيذ صحي طبيعي عضوي محلي عالمي رسمي خاص عام مجاني متاح مهم ضروري ممكن صعب سهل مناسب صحيح سريع ثابت مرن قابل ممتاز مميز فريد متنوع شامل مبدع مبتكر مسؤول محترف ماهر بارع مجتهد متفوق ناجح متعاون متواضع صبور مركز منتبه منظم مرتب دقيق واضح واثق هادف متوازن متكامل مستمر متجدد مفاجئ سعيد جميل رائع نشيط حيوي مريح عملي أنيق هادئ بسيط جذاب قوي ذكي سريع قريب بعيد هنا هناك الآن لاحقاً اليوم غداً أمس دائماً أحياناً غالباً نادراً أبداً أولاً ثانياً أخيراً سريعاً ببطء جيداً بهدوء بعناية بسهولة بوضوح بدقة معاً وحده كثيراً قليلاً تماماً تقريباً ربما بالتأكيد فعلاً جداً أيضاً فقط خاصة عامة مباشرة لاحقاً سابقاً مبكراً متأخراً صباحاً مساءً ليلاً نهاراً شتاء صيف ربيع خريف خميس جمعة سبت أحد اثنين ثلاثاء أربعاء يناير فبراير مارس أبريل مايو يونيو يوليو أغسطس سبتمبر أكتوبر نوفمبر ديسمبر رمضان عيد موسم بداية نهاية منتصف ساعة دقيقة لحظة فترة عصر جيل طفل شاب بالغ كبير عجوز رجل امرأة ولد بنت شخص إنسان فريق جماعة فرد جار صديق قريب زميل شريك أخ أخت أب أم جد جدة عم خال ابن ابنة زوج زوجة أسرة عائلة ضيف زائر مسافر سائح عامل موظف مدير مسؤول طبيب ممرض معلم طالب مهندس مبرمج مصمم فنان شاعر كاتب صحفي محامي قاضي شرطي رجل إطفاء طيار بحار سائق مزارع صياد نجار حداد خياط طباخ بائع تاجر مدير عالم باحث مخترع مخترعة لاعب مدرب حكم ممثل مخرج مصور موسيقي رسام نحات راقص مغني قارئ مترجم مرشد مستشار متطوع قائد عضو رئيس وزير سفير ملك أمير قائد جندي حارس عامل فني مختص خبير متدرب معلم مدرب تلميذ متعلم زميل صديق رفيق منافس بطل فائز خاسر متسابق متفرج جمهور مجموعة فريق شركة متجر مؤسسة منظمة جمعية نادي مركز مدرسة جامعة مكتبة مسرح متحف معرض قاعة غرفة مكتب مختبر مصنع ورشة مزرعة حقل حديقة ملعب موقف محطة مطار ميناء مرفأ سوق بنك مصرف مستشفى عيادة صيدلية مسجد جامعة كلية معهد مدرسة صف درس محاضرة دورة تدريب ورشة مؤتمر اجتماع لقاء ندوة حوار نقاش مناظرة عرض فعالية مهرجان مسابقة بطولة مباراة سباق حفل زفاف عيد مناسبة رحلة نزهة جولة زيارة عطلة إجازة سفر مغامرة تجربة مهمة مشروع خطة هدف فكرة حلم بحث دراسة عمل وظيفة مهنة خدمة طلب مساعدة دعم نصيحة سؤال جواب شرح معلومة بيانات دليل مصدر مرجع حقيقة رأي خبر تقرير مقال قصة رواية حكاية قصيدة نشيد أغنية لحن نغمة صوت صدى ضجيج سكون هدوء فرح سعادة حزن غضب خوف شجاعة أمل يأس حب كره ثقة شك صبر تعب نشاط راحة نوم حلم كابوس ذكرى مفاجأة خبر بشرى رسالة دعوة بطاقة هدية جائزة ميدالية كأس شهادة وسام نجاح تفوق إنجاز تقدم تطور تغيير تحسين نمو تعلم معرفة علم فهم وعي إدراك تركيز انتباه تفكير تخطيط تنظيم إدارة ترتيب اختيار قرار حل مشكلة تحدي فرصة احتمال نتيجة أثر سبب هدف وسيلة طريقة أسلوب نظام قاعدة قانون حق حرية عدالة مساواة احترام تعاون مشاركة مساعدة صداقة محبة رحمة لطف كرم شرف صدق أمانة إخلاص وفاء شجاعة تواضع حكمة صبر اجتهاد عزيمة إرادة نشاط طاقة صحة حياة طبيعة بيئة مجتمع ثقافة حضارة تاريخ جغرافيا اقتصاد سياسة أدب فن تقنية علم طب هندسة برمجة تصميم تعليم تدريب رياضة موسيقى تصوير رسم كتابة قراءة ترجمة صناعة زراعة تجارة سياحة نقل اتصال مواصلات إنترنت شبكة هاتف منصة تطبيق موقع برنامج نظام ملف قاعدة بيانات خادم جهاز أداة آلة محرك قطار سيارة طائرة سفينة حاسوب هاتف كاميرا شاشة لوحة مفاتيح فأرة سماعة مكبر صوت ميكروفون عدسة بطارية شاحن سلك زر مفتاح قفل مصباح ساعة منبه تلفاز مذياع راديو مكيف ثلاجة غسالة فرن مكنسة خلاط مقص إبرة خيط مطرقة مفك مسمار برغي منشار كماشة ميزان مقياس ترمومتر بوصلة منظار عدسة مجهر تلسكوب قمر صناعي صاروخ مركبة روبوت ذراع آلي مستشعر محول جهاز تحكم لوحة دائرة كهرباء طاقة شمسية طاقة رياح غاز نفط فحم ماء هواء تراب أرض نار خشب معدن حديد نحاس ألومنيوم فضة ذهب بلاتين زجاج كريستال ورق كرتون كتاب دفتر مجلة جريدة صحيفة رسالة بطاقة ظرف ملصق إعلان شعار رمز علامة خط كلمة حرف رقم رقمية حروف لوحة رسم صورة تصوير فيديو مقطع تسجيل ملف مجلد رابط صفحة نافذة شاشة موقع متجر تطبيق برنامج نظام منصة خوارزمية شفرة كود مطور مستخدم عميل زائر حساب اسم كلمة مرور هوية دخول خروج تسجيل حفظ حذف تعديل تحديث بحث مشاركة إرسال استقبال اتصال شبكة رسالة إشعار تنبيه تذكير موعد جدول قائمة عنصر خيار إعداد تفضيل لغة ترجمة واجهة تصميم تجربة ألوان خلفية إطار زر حقل نموذج بطاقة نافذة قائمة تبويب صفحة شريط عنوان شعار أيقونة صورة ملف صوت مقطع حركة انتقال ضغط لمسة حركة تأثير استجابة سرعة أداء استقرار جودة أمان خصوصية خطأ خلل عطل إصلاح صيانة تحديث إصدار نسخة نسخة احتياطية استعادة تشغيل توقف بدء إنهاء تحميل تنزيل رفع إرسال حفظ مشاركة نسخ لصق قص مسح حذف استبدال إضافة إنشاء بناء تصميم تطوير اختبار تجربة مراجعة تحسين تعليم تعلم تدريب ممارسة كتابة طباعة قراءة سرعة دقة إتقان مسابقة جولة نتيجة درجة نقطة مستوى سهل متوسط صعب تكرار جملة سوالف جريدة حرف كلمة حروف فقرة نص كتاب قصة هدف إنجاز مستخدم يوم شهر أسبوع ساعة دقيقة ثانية مرة محاولة تمرين راحة بداية نهاية مرحلة فرصة إنجاز مهارة عادة تعلم تركيز ترتيب تقدم نجاح هدف حلم مستقبل طريق خطوة حركة انطلاق وصول رحلة مسار اتجاه وجهة مدينة قرية ساحل جبل غابة بحر نهر سماء أرض شمس قمر نجمة سحابة مطر شجرة زهرة وردة عشب طائر حيوان سمكة حصان قط كلب أرنب أسد نمر فيل دب جمل بقرة خروف دجاجة حمامة عصفور فراشة نحلة نملة سلحفاة ثعلب ذئب غزال قرد زرافة حوت دولفين أخطبوط سلحفاة سحلية ضفدع تمساح بطريق نسر صقر بومة طاووس ديك دجاجة بطة أوزة نعامة كنغر باندا ثعلب قنفذ سنجاب فأر جرذ خفاش نملة جرادة صرصور يعسوب عنكبوت عقرب دودة محار لؤلؤة مرجان صدفة شاطئ موج رمل صخر بحر محيط نهر نبع عين بحيرة شلال سد جسر واد جبل تل قمة سفح واحة جزيرة بركان كهف غار غابة حقل مزرعة بستان حديقة شجرة نخلة زيتونة ليمونة برتقالة تفاحة موزة فراولة كرزة عنب تين تمر رمان خوخ مشمش برقوق كرز أناناس جوز لوز بندق فستق كاجو جزر خيار خس بصل ثوم فلفل بطاطا طماطم قرع يقطين كوسا باذنجان ملفوف قرنبيط بروكلي سبانخ فاصوليا بازلاء عدس حمص فول ذرة قمح شعير أرز شوفان خبز رغيف كعكة فطيرة حلوى بسكويت شوكولاتة عسل مربى زبدة جبن لبنة حليب لبن زبادي عصير شراب شاي قهوة ماء وجبة إفطار غداء عشاء مطبخ مطعم مقهى مخبز سوق متجر طبق صحن كوب كأس ملعقة شوكة سكين قدر مقلاة فرن موقد ثلاجة غسالة مكنسة سلة صندوق رف خزانة درج طاولة كرسي أريكة سرير وسادة بطانية سجادة ستارة نافذة باب جدار أرض سقف مصباح مفتاح قفل ساعة مرآة تلفاز حاسوب هاتف كتاب قلم دفتر حقيبة حذاء جورب قميص ثوب معطف قبعة وشاح نظارة خاتم سوار ساعة محفظة مفتاح نقود عملة ورقة بطاقة جواز تذكرة خريطة جريدة مجلة صحيفة كتاب قصة رواية قصيدة رسالة بريد عنوان طرد صندوق ظرف ختم توقيع سطر فقرة صفحة فصل باب غلاف ورقة كلمة حرف رمز رقم نقطة فاصلة علامة سؤال تعجب لغة عربية إنجليزية فرنسية إسبانية صينية يابانية تركية لهجة معنى مرادف مضاد جمع مفرد نحو صرف إملاء قراءة كتابة خط نسخ طباعة لوحة مفاتيح شاشة حاسوب مكتبة مدرسة جامعة طالب معلم درس صف فصل كتاب قلم ممحاة مسطرة واجب اختبار امتحان سؤال جواب شرح مثال تجربة مشروع بحث تقرير مقال عرض تقديمي محاضرة دورة تدريب شهادة درجة علامة نقطة نجاح فشل تقدير مادة علم رياضيات فيزياء كيمياء أحياء تاريخ جغرافيا أدب شعر فن رسم موسيقى رياضة حاسوب تقنية هندسة طب صحة طبيب ممرض مريض دواء علاج عيادة مستشفى صيدلية موعد فحص نتيجة تحليل وصفة إسعاف ضماد جهاز حرارة ضغط نبض قلب رئة دماغ عين أذن أنف فم يد ذراع كتف رأس شعر جلد عظم عضلة قدم ساق ركبة ظهر بطن إصبع ظفر سن لسان صوت رائحة طعم لمس نظر سمع ذاكرة روح جسم عقل صحة نوم راحة غذاء تمرين مشي ركض سباحة قفز لعب كرة مباراة سباق فريق لاعب مدرب حكم جمهور ملعب نادي كأس جائزة ميدالية بطولة تدريب مهارة قوة سرعة دقة تركيز تعاون هدف فوز خسارة تعادل نقطة نتيجة جولة محاولة نجاح خبرة طاقة حركة رياضة رحلة سفر طائرة قطار سيارة حافلة دراجة سفينة تذكرة جواز حقيبة فندق مطار محطة ميناء طريق شارع جسر نفق إشارة خريطة موقف وجهة رحلة عطلة نزهة سياحة مدينة دولة قرية عاصمة منطقة حي منزل بيت شقة غرفة مكتب مصنع متجر سوق مدرسة جامعة مستشفى حديقة متحف مسرح سينما مسجد كنيسة معبد محطة مطار ميناء فندق مقهى مطعم مكتبة معرض ملعب ساحة برج بناية شارع طريق جسر نفق حديقة شاطئ بحر جبل صحراء غابة مزرعة حقل جزيرة واحة واد نهر بحيرة شلال سد عين بئر كهف مغارة قمة وادي سهل تل هضبة أرض كوكب فضاء سماء شمس قمر نجم سحاب غيم مطر ثلج برق رعد ريح نسيم هواء عاصفة ضباب حرارة برودة طقس فصل ربيع صيف خريف شتاء موسم صباح فجر ضحى ظهر عصر مغرب مساء ليل نهار يوم أسبوع شهر سنة عام لحظة ثانية دقيقة ساعة موعد تقويم تاريخ عيد عطلة رحلة لقاء اجتماع حدث خبر مفاجأة بداية نهاية منتصف فترة زمن عصر جيل ماض حاضر مستقبل تاريخ وقت مكان شخص إنسان بشر رجل امرأة طفل شاب شيخ فتاة ولد بنت رضيع أب أم أبن ابنة أخ أخت جد جدة عم خال قريب جار صديق زميل شريك ضيف زائر مسافر سائح موظف عامل مدير مسؤول رئيس قائد معلم طالب طبيب مهندس فنان كاتب شاعر مبرمج مصمم صحفي لاعب مدرب طبيب ممرض سائق طيار بحار مزارع بائع تاجر طباخ نجار حداد خياط مصور ممثل مغني موسيقي رسام باحث عالم مخترع شرطي جندي حارس محامي قاضي وزير سفير ملك أمير رئيس قائد عضو فريق مجموعة أسرة عائلة مجتمع شعب أمة دولة شركة مؤسسة جمعية منظمة نادي مدرسة جامعة فريق فرقة زملاء أصدقاء جيران ناس جمهور سكان زوار عملاء مستخدمون أطفال شباب كبار أعضاء متطوعون متخصصون خبراء مبتدئون محترفون منافسون أبطال فائزون صناع مبدعون مخترعون علماء فنانين كتّاب قراء طلاب معلمون مهندسون أطباء ممرضون موظفون مديرون عمال بائعون سائقون مزارعون جنود رجال نساء أطفال أصدقاء جيران زملاء أعضاء ضيوف زوار مسافرون سياح جمهور فريق مجموعة مجتمع عائلة أسرة مدرسة جامعة مؤسسة شركة جمعية منظمة نادي مركز معرض متحف مسرح مكتبة مختبر ورشة مصنع مزرعة سوق متجر مقهى مطعم مستشفى عيادة صيدلية بنك مكتب بيت شقة غرفة منزل قصر برج حديقة ملعب محطة مطار ميناء شاطئ جزيرة غابة جبل صحراء قرية مدينة عاصمة دولة وطن قارة عالم كوكب فضاء مجرة مجرة درب التبانة نظام شمس نجم قمر كويكب مذنب كوكب أرض ماء هواء نار تراب حجر صخر معدن رمل طين خشب ورق قماش جلد زجاج بلاستيك معدن حديد نحاس ذهب فضة ألمنيوم كروم فولاذ طاقة كهرباء ضوء حرارة حركة قوة سرعة صوت رائحة لون شكل حجم وزن طول عرض ارتفاع عمق مسافة مساحة اتجاه موقع نقطة خط دائرة مربع مستطيل مثلث شكل زاوية مركز طرف جانب سطح قاعدة قمة بداية نهاية وسط حافة ظل نور شمس قمر نجوم بحر نهر شجرة زهرة طائر سمكة حيوان بيت كتاب قلم مدرسة سيارة هاتف ماء هواء خبز تمر ليل نهار صباح مساء حب أمل صبر فرح سلام حلم عمل علم فن وقت حياة وطن عائلة صديق مدينة طريق بحر جبل سماء أرض قصة لغة صوت كلمة حرف جملة فكرة هدف تدريب نجاح مهارة دقة سرعة تركيز ذاكرة معرفة تعاون راحة صحة رياضة سفر موسيقى تقنية تصميم برنامج موقع شاشة لوحة مفاتيح بطارية شبكة اتصال رسالة بريد حساب كلمة مرور اسم مستخدم ضيف زائر قارئ كاتب طالب معلم مدرب لاعب فريق جائزة كأس ميدالية نقطة نتيجة اختبار رحلة مشروع خطة فكرة تجربة سؤال جواب خبر قصة رواية مجلة جريدة صحيفة تقرير مقال كتاب صفحة فقرة عنوان حرف كلمة لغة لهجة معنى حرف صوت حرف علة همزة تاء ثاء جيم حاء خاء دال ذال راء زاي سين شين صاد ضاد طاء ظاء عين غين فاء قاف كاف لام ميم نون هاء واو ياء أبجدية حروف هجاء كتابة قراءة تعلم تدريب تعليم طباعة كتابة نص جملة كلمة صفحة تمرين اختبار مسابقة لعبة جولة فريق نقطة مرحلة بداية نهاية توقف تشغيل انطلاق استعداد فوز نتيجة سرعة دقة مهارة أداء تقدم محاولة نجاح سجل إحصاء معدل أفضل متوسط مجموع مجموع نقاط خبرة جائزة إنجاز هدف نمو عادة تطوير تحسين جودة تجربة واجهة مستخدم تطبيق موقع هاتف حاسوب برنامج نظام أمان خصوصية ملف بيانات خادم مصدر كود لغة برمجة دالة صفحة زر نافذة قائمة خيار إعداد محرك قاعدة شبكة اتصال إنترنت متصفح رابط عنوان إشعار رسالة بريد تنزيل تحميل حفظ إرسال استقبال مشاركة تدوين ملاحظة نسخ لصق بحث تسجيل حذف تحديث تشغيل إغلاق فتح إنشاء بناء إصلاح حل اختبار فحص مراجعة تحسين تطوير تصميم رسم صورة شعار رمز لون خط خلفية حركة انتقال تأثير استجابة لمس ضغط نقر صوت لمسة هزة شاشة لوحة مفاتيح مؤشر كتابة حذف رجوع إرسال لوحة حروف كتابة عربية خط أنيق كايرو عنوان mrtyping Typing practice focus speed accuracy finger keyboard word sentence story newspaper repetition confidence accuracy creativity consistency practice productivity progress result statistics achievements settings theme light dark color accent sound vibration support feedback inspiration challenge daily streak record level easy medium hard sentence story news repeat conversation start stop menu game player score point session round timer countdown target phrase text input match error typo correction backspace space key enter command bot assistant reply prompt welcome choose level training practice user interface phone mobile responsive safe area accessibility contrast language Arabic direction RTL font Cairo touch screen keyboard shortcut storage local preferences error loading empty state success badge achievement chart progress result statistics best score average accuracy words per minute minute timer duration restart next round home about title logo avatar identity brand design youth elegant modern quality fluency typing master daily rhythm focus flow glow glass blur gradient animation interactive friction rounded card panel bubble assistant message command practice habits progress streak record profile badge trophy focus target challenge time accuracy effort letter cursor keyboard key press response tactile subtle feedback vibration browser local game content prebuilt offline mode availability cache startup no external ai no network lexicon accessible no account password plain no fake login local data privacy device storage sessions reset clear confirmation level count word bank set unique content pool random avoid repeated immediate phrase maybe selection round memory last draws per game/difficulty each client local history."
"""

# English vocabulary bank; deduplication keeps the API contract exact.
EN_WORDS = """
house book sun moon road window garden school pen city sea car flower table phone computer time dream success friend water tree door room food travel rain cloud mountain river star morning evening family music idea game work memory language sound color story notebook bag key chair clock bread apple coffee bird fish child teacher doctor market village train plane ship energy sport health skill science art patience hope joy peace light stone sand snow fire air letter picture screen keyboard typing speed accuracy practice goal habit choice invention teamwork knowledge rest kitchen shoe shirt center theater concert library farm stadium airport restaurant hotel street bridge tunnel station beach desert oasis valley plain cloud lightning thunder spring summer autumn winter bird horse camel rabbit lion tiger deer wolf elephant bear butterfly bee ant sky soil breeze forest branch leaf root fruit cookery run jump walk swim ride solve build share learn speak listen explain answer question card mailbox lock curtain sofa carpet mirror calendar lamp drawing camera lens page book newspaper magazine journal paragraph title report article message invitation map passport suitcase ticket bus bike truck rail dock market cashier waiter baker chef fruit vegetable strawberry grape orange lemon banana peach date milk cheese rice meat chicken egg sugar honey salt salt pot ship harbour goal manager employee engineer programmer design mechanic scientist artist poet novelist writer reader learner coach mentor class group brother sister parent grandfather mother father guest visitor guard farmer shepherd nurse manager worker office manager merchant photographer singer dancer actor director lawyer judge soldier officer volunteer captain leader member president pilot sailor driver tailor carpenter blacksmith cook musician journalist translator adviser entrepreneur florist gardener butcher dentist vet barber plumber electrician technician investor designer developer user client visitor account privacy secure feature product solution progress update version release debug repair error issue bug test integration feedback support reliability performance quality experience journey action movement focus memory idea opinion decision challenge opportunity attempt result reason cause method process plan schedule calendar reminder achievement effort confidence patience habit discipline kindness respect trust safety care responsibility justice fairness generosity courage wisdom creativity innovation design color layout sound response touch reaction gesture haptic screen keyboard cursor field input output command instruction assistant bot menu option level easy medium hard practice drill test round session countdown target prompt story sentence article news repetition repeat vocabulary word phrase paragraph headline progress points score record best speed accuracy stats settings theme light dark modern elegant fresh calm confident quick agile focus clarity community profile badge trophy star medal rank goal streak daily weekly monthly improvement lesson exercise trial result complete finish start stop pause restart continue next previous home welcome hello thanks please sorry great excellent ready typing finger thumb key enter space backspace shift tab return command shortcut internet network browser website web app platform software program system file data folder source code function module server api request response success failure timeout loading saved cache local storage device phone tablet laptop screen camera photo icon logo avatar brand font Cairo Arabic English interface right-to-left left-to-right alignment contrast accessible reduced motion safe area touch target mobile viewport width height scroll resize error boundary state status idle busy waiting playing completed stopped muted select difficulty choose language help about terms privacy history export import reset profile user name display name role admin member contact support email account password login signup register security session token credential secret encryption authentication verification validation input output sanitize escape encode local offline online sync cloud backup restore deployment hosting build version pipeline package requirement dependency test coverage pytest unittest node python fastapi uvicorn api endpoint random sample words unique shuffle sample content generator code quality maintainability extensibility reliable mobile-first usability."
"""

AR_WORDS = tuple(dict.fromkeys(AR_WORD_BASE.split()))
# Keep a generous base list. For Arabic, add clitic forms only if a future edit
# shortens the curated list; all current practice tokens remain deterministic.
def _build_ar_word_tokens() -> tuple[str, ...]:
    tokens = list(AR_WORDS)
    for word in AR_WORDS:
        bare = word[2:] if word.startswith("ال") else word
        article = word if word.startswith("ال") else "ال" + word
        for form in (article, "و" + article, "ب" + article, "ل" + article, "و" + bare, "ب" + bare, "ل" + bare):
            if form not in tokens:
                tokens.append(form)
            if len(tokens) >= 350:
                return tuple(tokens[:350])
    raise RuntimeError("Arabic word bank must contain at least 350 unique practice forms")

AR_WORD_BANK = _build_ar_word_tokens()
EN_WORD_BANK = tuple(dict.fromkeys(EN_WORDS.split()))
if len(EN_WORD_BANK) < 350:
    # Inflected forms are useful typing tokens and keep English mode complete.
    for word in tuple(EN_WORD_BANK):
        for form in (word + "s", word + "ed", word + "ing"):
            if form not in EN_WORD_BANK:
                EN_WORD_BANK += (form,)
            if len(EN_WORD_BANK) >= 350:
                break
        if len(EN_WORD_BANK) >= 350:
            break
    if len(EN_WORD_BANK) < 350:
        raise RuntimeError("English word bank must contain at least 350 unique practice tokens")
EN_WORD_BANK = EN_WORD_BANK[:350]
AR_WORD_BANK = AR_WORD_BANK[:350]


def _make_sentences(language: str, difficulty: str) -> tuple[str, ...]:
    if difficulty == "easy":
        openers, endings = (AR_EASY_OPENERS, AR_EASY_ENDINGS) if language == "ar" else (EN_EASY_OPENERS, EN_EASY_ENDINGS)
        connector = "، " if language == "ar" else ", "
        return tuple(f"{opener}{connector}{ending}." for opener, ending in product(openers, endings))
    if difficulty == "medium":
        openers, actions, endings = (AR_MID_OPENERS, AR_MID_ACTIONS, AR_MID_ENDINGS) if language == "ar" else (EN_MID_OPENERS, EN_MID_ACTIONS, EN_MID_ENDINGS)
        connector = "، " if language == "ar" else ", "
        joiner = "، ثم " if language == "ar" else ", then "
    else:
        openers, actions, endings = (AR_HARD_OPENERS, AR_HARD_ACTIONS, AR_HARD_ENDINGS) if language == "ar" else (EN_HARD_OPENERS, EN_HARD_ACTIONS, EN_HARD_ENDINGS)
        connector = "، " if language == "ar" else ", "
        joiner = "، وبعد ذلك " if language == "ar" else ", and after that "
    return tuple(f"{opener}{connector}{action}{joiner}{ending}." for opener, action, ending in product(openers, actions, endings))


def _make_stories(language: str, difficulty: str) -> tuple[str, ...]:
    places, characters, goals, endings = (AR_PLACES, AR_CHARACTERS, AR_GOALS, AR_STORY_ENDINGS) if language == "ar" else (EN_PLACES, EN_CHARACTERS, EN_GOALS, EN_STORY_ENDINGS)
    rows = []
    for index, (place, character, ending) in enumerate(product(places, characters, endings)):
        goal = goals[(index * 7) % len(goals)]
        if language == "ar":
            if difficulty == "easy":
                rows.append(f"في {place}، عاش {character} يحلم بـ {goal}. وفي يوم، {ending}.")
            elif difficulty == "medium":
                rows.append(f"في {place}، قرر {character} أن يبدأ {goal}. وبعد أن واجه تحدياً بسيطاً، {ending}.")
            else:
                rows.append(f"في {place}، وضع {character} خطة طويلة من أجل {goal}. وعندما ظهرت عقبة غير متوقعة، تعاون مع الآخرين حتى {ending}، فعاد الجميع بخبرة جديدة.")
        else:
            if difficulty == "easy":
                rows.append(f"In {place}, {character} dreamed of {goal}. One day, {ending}.")
            elif difficulty == "medium":
                rows.append(f"In {place}, {character} decided to begin {goal}. After a small challenge, {ending}.")
            else:
                rows.append(f"In {place}, {character} made a careful plan for {goal}. When an unexpected obstacle appeared, they worked together until {ending}, and everyone gained new experience.")
    return tuple(rows)


def _make_news(language: str) -> tuple[str, ...]:
    places, events, reactions, goals = (AR_NEWS_PLACES, AR_NEWS_EVENTS, AR_NEWS_REACTIONS, AR_NEWS_GOALS) if language == "ar" else (EN_NEWS_PLACES, EN_NEWS_EVENTS, EN_NEWS_REACTIONS, EN_NEWS_GOALS)
    if language == "ar":
        return tuple(
            f"في {place}، أُعلن عن {event}، وسط {reactions[variant]}، بهدف {goals[(place_index + event_index + variant) % len(goals)]}."
            for place_index, place in enumerate(places)
            for event_index, event in enumerate(events)
            for variant in range(len(reactions))
        )
    return tuple(
        f"In {place}, officials announced {event}, amid {reactions[variant]}, to {goals[(place_index + event_index + variant) % len(goals)]}."
        for place_index, place in enumerate(places)
        for event_index, event in enumerate(events)
        for variant in range(len(reactions))
    )

CONTENT: dict[str, dict[str, dict[str, tuple[str, ...]]]] = {}
for _language in ("ar", "en"):
    CONTENT[_language] = {
        "sentences": {level: _make_sentences(_language, level) for level in ("easy", "medium", "hard")},
        "stories": {level: _make_stories(_language, level) for level in ("easy", "medium", "hard")},
        "news": {level: _make_news(_language) for level in ("easy", "medium", "hard")},
        "repeat": {level: AR_WORD_BANK if _language == "ar" else EN_WORD_BANK for level in ("easy", "medium", "hard")},
    }

# Verify the explicit content contract at startup so a future content edit can
# never silently reintroduce an infinite generation loop.
for _language in ("ar", "en"):
    for _level in ("easy", "medium", "hard"):
        assert len(CONTENT[_language]["sentences"][_level]) == 400
        assert len(CONTENT[_language]["stories"][_level]) == 500
        assert len(CONTENT[_language]["news"][_level]) == 400
        assert len(CONTENT[_language]["repeat"][_level]) == 350
        assert len(set(CONTENT[_language]["sentences"][_level])) == 400
        assert len(set(CONTENT[_language]["stories"][_level])) == 500
        assert len(set(CONTENT[_language]["news"][_level])) == 400


@app.get("/", response_class=HTMLResponse)
async def serve_app() -> HTMLResponse:
    return HTMLResponse(HTML_PAGE)


@app.get("/api/target")
async def get_target(
    game: Literal["stories", "news", "sentences", "repeat"],
    difficulty: Literal["easy", "medium", "hard"] = "medium",
    language: Literal["ar", "en"] = "ar",
    count: int | None = Query(default=None, ge=1, le=20),
) -> dict[str, str | int]:
    if game == "repeat":
        if count is None or not 1 <= count <= 20:
            raise HTTPException(status_code=422, detail="Repeat mode requires a word count from 1 to 20")
        bank = CONTENT[language][game][difficulty]
        words = random.sample(bank, count)
        # Each selected token is repeated exactly three times, as requested.
        target = " ".join(word for word in words for _ in range(3))
        display = target
        return {"game": game, "difficulty": difficulty, "language": language, "target": target, "display": display, "pool_size": len(bank), "word_count": count}
    pool = CONTENT[language][game][difficulty]
    target = random.choice(pool)
    return {"game": game, "difficulty": difficulty, "language": language, "target": target, "display": target, "pool_size": len(pool), "word_count": 0}


HTML_PAGE = r'''<!doctype html>
<html lang="ar" dir="rtl" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,interactive-widget=resizes-content">
<meta name="theme-color" content="#090b12">
<meta name="description" content="mr.typing — مساحة عربية أنيقة للتدرب على سرعة الكتابة ودقتها.">
<title>mr.typing — اكتب بطريقتك</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{color-scheme:dark;--bg:#090b12;--bg-soft:#10131d;--panel:rgba(21,25,37,.78);--panel-solid:#151925;--surface:rgba(255,255,255,.055);--surface-2:rgba(255,255,255,.085);--text:#f5f7ff;--muted:#9ba4ba;--border:rgba(255,255,255,.09);--accent:#a78bfa;--accent-2:#56d4e7;--accent-soft:rgba(167,139,250,.16);--success:#56d8a4;--danger:#ff7282;--warning:#ffcb78;--shadow:0 24px 70px rgba(0,0,0,.32);--font:"Cairo",system-ui,-apple-system,"Segoe UI",sans-serif;--radius:24px}
html[data-theme="light"]{color-scheme:light;--bg:#f3f5fa;--bg-soft:#e9edf6;--panel:rgba(255,255,255,.78);--panel-solid:#fff;--surface:rgba(20,26,42,.045);--surface-2:rgba(20,26,42,.075);--text:#161b2a;--muted:#687187;--border:rgba(27,34,54,.10);--accent:#7149d7;--accent-2:#138ca1;--accent-soft:rgba(113,73,215,.11);--success:#15845e;--danger:#c93650;--warning:#a96000;--shadow:0 24px 70px rgba(39,49,73,.12)}
*{box-sizing:border-box}html,body{height:100%;margin:0}body{min-height:100dvh;background:radial-gradient(ellipse at 85% -10%,rgba(103,83,193,.18),transparent 34%),radial-gradient(ellipse at 5% 100%,rgba(36,164,184,.12),transparent 34%),var(--bg);color:var(--text);font-family:var(--font);-webkit-font-smoothing:antialiased}button,input{font:inherit}button{color:inherit;border:0;cursor:pointer;-webkit-tap-highlight-color:transparent}button:focus-visible,input:focus-visible{outline:3px solid color-mix(in srgb,var(--accent) 72%,transparent);outline-offset:2px}.shell{width:min(100%,1120px);min-height:100dvh;margin:auto;padding:18px clamp(14px,4vw,42px) calc(22px + env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:18px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:5px 0}.brand{display:flex;align-items:center;gap:11px;font-size:18px;font-weight:900;letter-spacing:.01em}.brand b{color:var(--accent-2)}.mark{width:42px;height:42px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.15);border-radius:15px;background:linear-gradient(145deg,#aa88ff,#4fcde0);box-shadow:0 9px 28px rgba(122,102,224,.27)}.mark svg{width:25px;height:25px}.status-pill{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:12px;padding:8px 13px;border-radius:999px;border:1px solid var(--border);background:var(--surface)}.status-dot{width:7px;height:7px;border-radius:50%;background:var(--success);box-shadow:0 0 12px color-mix(in srgb,var(--success) 65%,transparent)}.layout{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:18px;align-items:stretch;flex:1;min-height:0}.panel{border:1px solid var(--border);border-radius:var(--radius);background:var(--panel);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);box-shadow:var(--shadow)}.chat-panel{min-height:min(74dvh,760px);height:100%;display:flex;flex-direction:column;overflow:hidden}.chat-head{display:flex;align-items:center;gap:12px;padding:18px 20px;border-bottom:1px solid var(--border)}.bot-mark{width:42px;height:42px;border-radius:15px;display:grid;place-items:center;background:linear-gradient(145deg,#aa88ff,#4fcde0);box-shadow:0 8px 24px rgba(122,102,224,.25)}.bot-mark svg{width:24px;height:24px}.chat-head h1{font-size:15px;margin:0;font-weight:800}.chat-head p{margin:2px 0 0;color:var(--muted);font-size:11px}.chat-head .spacer{flex:1}.icon-button{width:38px;height:38px;display:grid;place-items:center;border:1px solid var(--border);border-radius:13px;background:var(--surface);color:var(--muted);transition:transform .18s,background .18s}.icon-button:hover{background:var(--surface-2)}.icon-button:active,.choice:active,.send:active,.tab:active{transform:scale(.96)}.icon-button svg,.send svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.chat-log{flex:1;min-height:260px;overflow:auto;padding:20px clamp(14px,3vw,26px);display:flex;flex-direction:column;gap:14px;scroll-behavior:smooth;overscroll-behavior:contain}.welcome-note{align-self:center;text-align:center;color:var(--muted);font-size:11px;padding:3px 10px 8px}.message{max-width:min(86%,660px);display:flex;gap:9px;align-items:flex-end;animation:arrive .24s ease-out}.message.user{align-self:flex-start;flex-direction:row-reverse}.message.bot{align-self:flex-end}.avatar{width:29px;height:29px;border-radius:11px;background:linear-gradient(145deg,#aa88ff,#4fcde0);display:grid;place-items:center;flex:none;color:white;font-weight:900;font-size:15px}.avatar.user-avatar{background:var(--surface-2);border:1px solid var(--border);color:var(--text);font-size:11px}.bubble{padding:11px 14px;border:1px solid var(--border);border-radius:18px;background:var(--surface);font-size:14px;line-height:1.8;white-space:pre-wrap;overflow-wrap:anywhere}.message.user .bubble{background:linear-gradient(135deg,#7552cf,#338fa8);color:#fff;border-color:transparent;border-bottom-right-radius:6px}.message.bot .bubble{border-bottom-left-radius:6px}.message.system .bubble{color:var(--muted);font-size:12px}.message.result .bubble{border-color:color-mix(in srgb,var(--success) 30%,var(--border));background:color-mix(in srgb,var(--success) 7%,var(--surface))}.choice-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:12px}.choice{min-height:47px;padding:10px 12px;border:1px solid var(--border);border-radius:15px;background:var(--surface);font-size:13px;font-weight:700;transition:transform .16s,border-color .16s,background .16s}.choice:hover{border-color:color-mix(in srgb,var(--accent) 50%,var(--border));background:var(--accent-soft)}.choice small{display:block;font-size:10px;color:var(--muted);font-weight:500;margin-top:2px}.choice.level{min-height:43px}.message-body{min-width:0}.typing-zone{padding:0 18px 15px}.target-card{border:1px solid var(--border);border-radius:18px;background:linear-gradient(135deg,var(--surface-2),var(--surface));padding:15px 16px;margin-bottom:10px}.target-label{font-size:10px;color:var(--muted);margin-bottom:7px;display:flex;justify-content:space-between;gap:8px}.target{font-size:16px;line-height:2;font-weight:700;word-break:break-word}.target span.correct{color:var(--success)}.target span.wrong{color:var(--danger);text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px}.target span.current{box-shadow:inset 0 -2px var(--accent)}.typing-input{width:100%;min-height:54px;resize:vertical;border:1px solid var(--border);border-radius:16px;background:var(--bg-soft);color:var(--text);padding:13px 15px;font-size:15px;line-height:1.7;direction:auto;transition:border-color .18s,box-shadow .18s}.typing-input:focus{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-soft);outline:none}.live-stats{display:flex;justify-content:space-between;gap:12px;color:var(--muted);font-size:11px;padding:9px 3px 0}.live-stats strong{color:var(--text);font-size:12px}.chat-compose{display:flex;gap:9px;align-items:center;padding:13px 15px calc(13px + env(safe-area-inset-bottom));border-top:1px solid var(--border);background:color-mix(in srgb,var(--panel-solid) 78%,transparent)}.chat-input{min-width:0;flex:1;height:47px;padding:0 15px;border:1px solid var(--border);border-radius:15px;background:var(--surface);color:var(--text);font-size:13px}.chat-input::placeholder,.typing-input::placeholder{color:var(--muted)}.send{width:47px;height:47px;display:grid;place-items:center;border-radius:15px;background:linear-gradient(145deg,#8b6be3,#36a9bb);color:#fff;box-shadow:0 8px 22px rgba(95,93,188,.2);transition:transform .16s,filter .16s}.send:hover{filter:brightness(1.08)}.side{display:flex;flex-direction:column;gap:14px}.side-card{padding:18px}.side-card h2{margin:0 0 12px;font-size:13px;font-weight:800}.side-card p{margin:0;color:var(--muted);font-size:12px;line-height:1.8}.stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}.stat{border:1px solid var(--border);border-radius:16px;padding:12px;background:var(--surface)}.stat span{display:block;color:var(--muted);font-size:10px}.stat strong{display:block;margin-top:3px;font-size:20px;letter-spacing:-.04em}.tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;padding:7px;border-radius:17px;background:var(--surface);border:1px solid var(--border)}.tab{padding:9px 6px;border-radius:12px;background:transparent;color:var(--muted);font-size:11px;font-weight:700;transition:transform .16s,background .16s,color .16s}.tab.active{background:var(--panel-solid);color:var(--text);box-shadow:0 5px 18px rgba(0,0,0,.08)}.tab svg{display:block;margin:0 auto 4px;width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.quick-note{display:flex;align-items:flex-start;gap:10px;padding:12px;border-radius:16px;background:var(--accent-soft);color:var(--text);font-size:11px;line-height:1.8}.quick-note b{color:var(--accent)}.feature-placeholder{border:1px solid var(--border);border-radius:16px;padding:13px;background:var(--surface)}.feature-placeholder p{margin-top:10px}.feature-badge{display:inline-flex;padding:4px 9px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-size:10px;font-weight:800}.feature-actions{display:flex;gap:8px;margin-top:12px}.feature-actions button{flex:1;padding:9px;border:1px solid var(--border);border-radius:11px;background:var(--surface);color:var(--muted);font-size:10px;font-weight:700;opacity:.65;cursor:not-allowed}.setting-row{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 0;border-bottom:1px solid var(--border);font-size:12px}.setting-row:last-child{border-bottom:0}.setting-row select{max-width:145px;border:1px solid var(--border);border-radius:10px;padding:7px 9px;background:var(--panel-solid);color:var(--text);font-family:var(--font);font-size:11px}.text-button{background:transparent;color:var(--danger);font-size:11px;font-weight:700;padding:7px}.footer{text-align:center;color:var(--muted);font-size:10px;padding:2px 0 0}.hidden{display:none!important}.thinking{display:inline-flex;gap:4px;padding:5px 2px}.thinking i{width:5px;height:5px;border-radius:50%;background:var(--muted);animation:bop .9s infinite ease-in-out}.thinking i:nth-child(2){animation-delay:.14s}.thinking i:nth-child(3){animation-delay:.28s}@keyframes bop{0%,60%,100%{transform:translateY(0);opacity:.45}30%{transform:translateY(-4px);opacity:1}}@keyframes arrive{from{opacity:0;transform:translateY(7px) scale(.985)}to{opacity:1;transform:translateY(0) scale(1)}}
@media(max-width:840px){.layout{grid-template-columns:1fr}.chat-panel{min-height:58dvh}.side{display:grid;grid-template-columns:1fr 1fr}.side-card:last-child{grid-column:1/-1}}
@media(max-width:560px){.shell{padding:10px 11px calc(12px + env(safe-area-inset-bottom));gap:11px}.topbar{padding:2px 2px}.brand{font-size:16px}.mark{width:37px;height:37px;border-radius:13px}.status-pill{font-size:10px;padding:7px 10px}.chat-panel{min-height:0;height:calc(100dvh - 87px - env(safe-area-inset-bottom));border-radius:21px}.chat-head{padding:13px 14px}.chat-log{padding:15px 12px;min-height:130px}.message{max-width:92%}.bubble{font-size:13px;padding:10px 12px}.typing-zone{padding:0 11px 10px}.target-card{padding:12px}.target{font-size:14px}.chat-compose{padding:10px 11px calc(10px + env(safe-area-inset-bottom))}.chat-input{height:45px}.send{width:45px;height:45px}.side{grid-template-columns:1fr}.side-card:last-child{grid-column:auto}.footer{display:none}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
</style>
</head>
<body>
<div class="shell">
  <header class="topbar">
    <div class="brand"><span class="mark" aria-hidden="true"><svg viewBox="0 0 40 40"><path d="M10 11h20M20 11v19" fill="none" stroke="white" stroke-width="5" stroke-linecap="round"/><circle cx="29" cy="29" r="2.5" fill="white"/></svg></span><span>mr.<b>typing</b></span></div>
    <div class="status-pill"><span class="status-dot" id="statusDot"></span><span id="statusText">جاهز للتدريب</span></div>
  </header>
  <div class="layout">
    <section class="panel chat-panel" id="chatPanel" aria-label="محادثة التدريب">
      <div class="chat-head">
        <div class="bot-mark" aria-hidden="true"><svg viewBox="0 0 40 40"><path d="M10 11h20M20 11v19" fill="none" stroke="white" stroke-width="5" stroke-linecap="round"/><circle cx="29" cy="29" r="2.5" fill="white"/></svg></div>
        <div><h1 id="botTitle">رفيق الكتابة</h1><p id="botCaption">تدريب خفيف، تقدّم واضح</p></div>
        <div class="spacer"></div>
        <button class="icon-button" id="clearChat" aria-label="بدء محادثة جديدة" title="محادثة جديدة"><svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 0 0-14.9-3M4 4v4h4M4 13a8 8 0 0 0 14.9 3M20 20v-4h-4"/></svg></button>
      </div>
      <div class="chat-log" id="chatLog" role="log" aria-live="polite" aria-relevant="additions text"></div>
      <div class="typing-zone hidden" id="typingZone"></div>
      <form class="chat-compose" id="chatForm" autocomplete="off">
        <input class="chat-input" id="chatInput" placeholder="اكتب أمرًا أو اختر لعبة…" aria-label="أرسل رسالة إلى رفيق الكتابة" maxlength="120">
        <button class="send" id="sendButton" type="submit" aria-label="إرسال"><svg viewBox="0 0 24 24"><path d="M4 12 20 4l-5 16-3.5-6.5L4 12Z"/><path d="m11.5 13.5 4-4"/></svg></button>
      </form>
    </section>
    <aside class="side" id="sidePanel" aria-label="لوحة المعلومات">
      <section class="panel side-card">
        <h2 id="spaceTitle">مساحتك</h2>
        <div class="tabs" id="tabs" role="tablist" aria-label="الأقسام">
          <button class="tab active" data-tab="home" role="tab" aria-selected="true"><svg viewBox="0 0 24 24"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-6v-7h-4v7H4a1 1 0 0 1-1-1V10Z"/></svg><span data-ui="homeTab">التدريب</span></button>
          <button class="tab" data-tab="stats" role="tab" aria-selected="false"><svg viewBox="0 0 24 24"><path d="M4 19V5m0 14h17M8 15l3-4 3 2 5-7"/></svg><span data-ui="statsTab">إحصاءاتي</span></button>
          <button class="tab" data-tab="settings" role="tab" aria-selected="false"><svg viewBox="0 0 24 24"><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="m19 13 2 1-2 4-2-1-2 1v2H9v-2l-2-1-2 1-2-4 2-1v-2l-2-1 2-4 2 1 2-1V4h6v2l2 1 2-1 2 4-2 1v2Z"/></svg><span data-ui="settingsTab">الإعدادات</span></button>
          <button class="tab" data-tab="leaderboard" role="tab" aria-selected="false"><svg viewBox="0 0 24 24"><path d="M8 4h8v5a4 4 0 0 1-8 0V4Z"/><path d="M8 6H5v2a3 3 0 0 0 3 3m8-5h3v2a3 3 0 0 1-3 3M10 16h4m-2-3v3m-3 3h6"/></svg><span data-ui="leaderboardTab">المتصدرون</span></button>
          <button class="tab" data-tab="community" role="tab" aria-selected="false"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2m2-9a3 3 0 1 0 0-6m4 15v-2a6 6 0 0 0-4-5.7"/></svg><span data-ui="communityTab">المجتمع</span></button>
          <button class="tab" data-tab="vip" role="tab" aria-selected="false"><svg viewBox="0 0 24 24"><path d="m12 3 2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.3l-5.2 2.8 1-5.8L3.5 9.2l5.9-.9L12 3Z"/></svg><span data-ui="vipTab">VIP</span></button>
          <button class="tab" data-tab="account" role="tab" aria-selected="false"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg><span data-ui="accountTab">الحساب</span></button>
        </div>
      </section>
      <section class="panel side-card" id="sideContent"></section>
      <section class="panel side-card">
        <h2 id="quickTitle">طريقة اللعب</h2>
        <div class="quick-note"><span aria-hidden="true">✦</span><span id="quickNoteText">اكتب ابدا لعرض الألعاب، أو اختر اللعبة مباشرة. وفي أي وقت اكتب وقف لإيقاف الجولة.</span></div>
      </section>
    </aside>
  </div>
  <footer class="footer" id="footerText">mr.typing · بيانات التدريب محفوظة على هذا الجهاز فقط</footer>
</div>
<script>
"use strict";
const $ = (selector, root=document) => root.querySelector(selector);
const $$ = (selector, root=document) => [...root.querySelectorAll(selector)];
const STRINGS = {
  ar:{menu:"ارحب ياطباع! هذي الألعاب اللي عندنا الحين:", games:[['سوالف','stories','حكايات قصيرة'],['جريدة','news','عناوين متنوعة'],['تكرار','repeat','ثبّت الكلمات'],['جمل','sentences','تدرّب على الجمل']], chooseDifficulty:"اختر المستوى المناسب:", difficulty:[['سهل','easy'],['متوسط','medium'],['صعب','hard']], repeatPrompt:"اختار عدد الكلمات المعروضه في التكرار من واحد إلى عشرين كلمة", invalidCount:"الرجاء إدخال رقم صحيح من 1 إلى 20.", stopped:"تم إيقاف البوت والجولة. اكتب «ابدا» لاستئناف التدريب.", resumed:"أهلًا بعودتك! اختر لعبة للبدء.", unknown:"ما فهمت الأمر. اكتب «ابدا» لعرض قائمة الألعاب.", typePrompt:"اكتب النص في مربع التدريب الظاهر أسفل المحادثة.", preparing:"جاري تجهيز الجولة…", go:"انطلق!", ready:"استعد!", repeatInfo:"كل كلمة ستظهر ثلاث مرات متتالية.", pool:"عنصر متاح في مكتبة التدريب", success:"أحسنت! أكملت الجولة.", next:"جولة جديدة", back:"قائمة الألعاب", finished:"الجولة مكتملة", accuracy:"الدقة", wpm:"كلمة/دقيقة", score:"نقطة", count:"الجولات", best:"أفضل سرعة", total:"إجمالي النقاط", emptyStats:"ابدأ أول جولة لترى تقدّمك هنا.", settings:"المظهر", theme:"السمة", language:"اللغة", dark:"داكن", light:"فاتح", arabic:"العربية", english:"English", reset:"مسح الإحصاءات على هذا الجهاز", resetConfirm:"هل تريد مسح الإحصاءات المحفوظة على هذا الجهاز؟", resetDone:"تم مسح الإحصاءات.", error:"تعذر تجهيز الجولة الآن. تحقق من الاتصال ثم حاول مجددًا.", botMuted:"البوت متوقف مؤقتًا. اكتب «ابدا» لاستئنافه.", ariaInput:"اكتب النص المعروض هنا", typingHint:"ابدأ الكتابة لاحتساب السرعة والدقة", level:"المستوى", wordsAvailable:"كلمة تدريبية في المكتبة", roundWord:"عدد الكلمات", commandPlaceholder:"اكتب أمرًا أو اختر لعبة…", cancelled:"ألغيت الجولة الحالية."},
  en:{menu:"Welcome! Choose a typing game:", games:[['Stories','stories','Short story passages'],['News','news','Fresh headline-style text'],['Repeat','repeat','Build word rhythm'],['Sentences','sentences','Practice complete sentences']], chooseDifficulty:"Choose your level:", difficulty:[['Easy','easy'],['Medium','medium'],['Hard','hard']], repeatPrompt:"Choose how many repeat words to display (from 1 to 20)", invalidCount:"Enter a whole number from 1 to 20.", stopped:"The bot and round are stopped. Type “start” to resume.", resumed:"Welcome back! Choose a game to begin.", unknown:"I didn’t understand. Type “start” to see the games.", typePrompt:"Type the text in the practice box below the chat.", preparing:"Preparing your round…", go:"Go!", ready:"Get ready!", repeatInfo:"Each selected word will appear three times in a row.", pool:"items in the practice library", success:"Nice work! Round complete.", next:"New round", back:"Game menu", finished:"Round complete", accuracy:"Accuracy", wpm:"WPM", score:"points", count:"Rounds", best:"Best speed", total:"Total points", emptyStats:"Complete your first round to see progress here.", settings:"Appearance", theme:"Theme", language:"Language", dark:"Dark", light:"Light", arabic:"العربية", english:"English", reset:"Clear this device’s stats", resetConfirm:"Clear the statistics saved on this device?", resetDone:"Statistics cleared.", error:"Could not prepare the round. Check your connection and try again.", botMuted:"The bot is paused. Type “start” to resume.", ariaInput:"Type the displayed text here", typingHint:"Start typing to track speed and accuracy", level:"Level", wordsAvailable:"practice words in the library", roundWord:"Words in this round", commandPlaceholder:"Type a command or choose a game…", cancelled:"The current round was cancelled."}
};
let language = safeRead('mrtyping.language','ar');
if(language !== 'ar' && language !== 'en') language = 'ar';
let theme = safeRead('mrtyping.theme','dark');
if(theme !== 'dark' && theme !== 'light') theme = 'dark';
let stats = safeRead('mrtyping.stats',{rounds:0,bestWpm:0,totalPoints:0,totalAccuracy:0});
let state = 'idle';
let currentGame = '';
let currentDifficulty = 'medium';
let repeatCount = 0;
let targetText = '';
let startedAt = 0;
let muted = false;
let timers = new Set();
let generation = 0;
let activeRequest = null;
let activeTab = 'home';
let chatStarted = false;

function safeRead(key, fallback){try{const value=localStorage.getItem(key);return value===null?fallback:JSON.parse(value)}catch{return fallback}}
function safeWrite(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true}catch{return false}}
function t(key){return STRINGS[language][key] ?? STRINGS.en[key] ?? key}
function gameNames(){return Object.fromEntries(STRINGS[language].games.map(([label,key])=>[label.toLocaleLowerCase(),key]))}
function canonicalCommand(value){return value.normalize('NFC').trim().toLocaleLowerCase().replace(/[أإآ]/g,'ا').replace(/[ًٌٍَُِّْـ]/g,'').replace(/\s+/g,' ')}
function displayGame(game){return STRINGS[language].games.find(([,key])=>key===game)?.[0] ?? game}
function displayLevel(level){return STRINGS[language].difficulty.find(([,key])=>key===level)?.[0] ?? level}
function saveStats(){safeWrite('mrtyping.stats',stats);renderSide()}
function setStatus(text, stopped=false){$('#statusText').textContent=text;$('#statusDot').style.background=stopped?'var(--muted)':'var(--success)'}
function clearTimers(){for(const timer of timers)clearTimeout(timer);timers.clear();$$('[data-thinking="true"]').forEach(node=>node.remove());generation++;if(activeRequest){activeRequest.abort();activeRequest=null}}
function later(callback,delay){const token=generation;const timer=setTimeout(()=>{timers.delete(timer);if(token===generation&&!muted)callback()},delay);timers.add(timer);return timer}
function cancelRound(){clearTimers();state='idle';targetText='';startedAt=0;$('#typingZone').classList.add('hidden');$('#typingZone').replaceChildren()}
function scrollChat(){const log=$('#chatLog');log.scrollTop=log.scrollHeight}
function addMessage(text,who='bot',options={}){
  const log=$('#chatLog');const row=document.createElement('div');row.className=`message ${who}${options.result?' result':''}`;
  const avatar=document.createElement('div');avatar.className=`avatar${who==='user'?' user-avatar':''}`;avatar.textContent=who==='user'?(language==='ar'?'أ':'Y'):'T';avatar.setAttribute('aria-hidden','true');
  const body=document.createElement('div');body.className='message-body';const bubble=document.createElement('div');bubble.className='bubble';bubble.textContent=text;body.append(bubble);
  if(options.choices){const grid=document.createElement('div');grid.className='choice-grid';for(const item of options.choices){const button=document.createElement('button');button.type='button';button.className=`choice${options.choiceType==='level'?' level':''}`;button.textContent=item.label;if(item.hint){const small=document.createElement('small');small.textContent=item.hint;button.append(small)}button.dataset.action=item.action;button.dataset.value=item.value;grid.append(button)}body.append(grid)}
  if(options.resultButtons){const grid=document.createElement('div');grid.className='choice-grid';for(const item of options.resultButtons){const button=document.createElement('button');button.type='button';button.className='choice';button.textContent=item.label;button.dataset.action=item.action;button.dataset.value=item.value;grid.append(button)}body.append(grid)}
  row.append(avatar,body);log.append(row);scrollChat();return row;
}
function addThinking(){const row=document.createElement('div');row.className='message bot';row.dataset.thinking='true';const avatar=document.createElement('div');avatar.className='avatar';avatar.textContent='T';const bubble=document.createElement('div');bubble.className='bubble';bubble.setAttribute('aria-label',language==='ar'?'يكتب':'typing');const dots=document.createElement('span');dots.className='thinking';for(let i=0;i<3;i++)dots.append(document.createElement('i'));bubble.append(dots);row.append(avatar,bubble);$('#chatLog').append(row);scrollChat();return row}
function reply(text,options={}){if(muted)return;const thinking=addThinking();later(()=>{thinking.remove();addMessage(text,'bot',options)},220)}
function menuChoices(){return STRINGS[language].games.map(([label,key,hint])=>({label,hint,action:'game',value:key}))}
function showMenu(){if(muted)return;state='idle';currentGame='';$('#typingZone').classList.add('hidden');$('#typingZone').replaceChildren();reply(t('menu'),{choices:menuChoices()});setStatus(language==='ar'?'جاهز للتدريب':'Ready to practice')}
function startGame(game){if(muted)return;cancelRound();currentGame=game;$('#typingZone').classList.add('hidden');addMessage(displayGame(game),'user');if(game==='repeat'){state='repeat-count';reply(t('repeatPrompt'));if(language==='ar')reply(t('repeatInfo'));return}state='difficulty';reply(t('chooseDifficulty'),{choices:STRINGS[language].difficulty.map(([label,value])=>({label,action:'difficulty',value})),choiceType:'level'})}
function chooseDifficulty(level){if(muted)return;currentDifficulty=level;state='countdown';beginCountdown()}
function normalizeDigits(value){return value.replace(/[٠-٩۰-۹]/g,ch=>String('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹'.indexOf(ch)%10))}
function acceptRepeatCount(value){const ascii=normalizeDigits(value);if(!/^\d{1,2}$/.test(ascii)){reply(t('invalidCount'));return}const number=Number(ascii);if(number<1||number>20){reply(t('invalidCount'));return}repeatCount=number;currentDifficulty='medium';state='countdown';beginCountdown()}
function beginCountdown(){if(muted)return;clearTimers();state='countdown';reply(t('preparing'));const token=generation;let n=3;const tick=()=>{if(token!==generation||muted)return;if(n>0){addMessage(String(n),'bot',{system:true});n--;later(tick,650);return}addMessage(t('go'),'bot',{system:true});later(()=>loadTarget(token),380)};later(tick,280)}
async function loadTarget(token){if(muted||token!==generation)return;state='loading';try{const params=new URLSearchParams({game:currentGame,difficulty:currentDifficulty,language});if(currentGame==='repeat')params.set('count',String(repeatCount));activeRequest=new AbortController();const response=await fetch(`/api/target?${params}`,{signal:activeRequest.signal,headers:{'Accept':'application/json'}});activeRequest=null;if(!response.ok)throw new Error(`HTTP ${response.status}`);const data=await response.json();if(token!==generation||muted)return;targetText=data.target;renderTyping(data);state='playing';setStatus(language==='ar'?'جولتك جارية':'Round in progress')}catch(error){if(error.name==='AbortError')return;if(token!==generation||muted)return;state='idle';reply(t('error'),{resultButtons:[{label:t('back'),action:'menu',value:''}]});setStatus(language==='ar'?'تعذر التحميل':'Could not load',true)}}
function renderTyping(data){const zone=$('#typingZone');zone.replaceChildren();zone.classList.remove('hidden');const card=document.createElement('div');card.className='target-card';const label=document.createElement('div');label.className='target-label';const kind=document.createElement('span');kind.textContent=`${displayGame(data.game)} · ${displayLevel(data.difficulty)}`;const size=document.createElement('span');size.textContent=data.game==='repeat'?`${data.word_count} ${t('roundWord')} · ${data.pool_size} ${t('wordsAvailable')}`:`${data.pool_size} ${t('pool')}`;label.append(kind,size);const target=document.createElement('div');target.className='target';target.id='targetText';target.dir='auto';for(const char of data.display){const span=document.createElement('span');span.textContent=char;target.append(span)}card.append(label,target);const input=document.createElement('textarea');input.className='typing-input';input.id='typingInput';input.rows=2;input.autocomplete='off';input.autocapitalize='off';input.spellcheck=false;input.maxLength=targetText.length;input.placeholder=t('typingHint');input.setAttribute('aria-label',t('ariaInput'));input.addEventListener('input',()=>onType(input.value));input.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();stopBot(true)}});const statsLine=document.createElement('div');statsLine.className='live-stats';statsLine.innerHTML=`<span>${t('wpm')}: <strong id="liveWpm">0</strong></span><span>${t('accuracy')}: <strong id="liveAccuracy">100%</strong></span>`;zone.append(card,input,statsLine);setTimeout(()=>input.focus({preventScroll:true}),50)}
function onType(value){if(state!=='playing')return;if(value.length&&!startedAt)startedAt=performance.now();const spans=$$('#targetText span');let correct=0;let mistakes=0;for(let i=0;i<spans.length;i++){spans[i].classList.remove('correct','wrong','current');if(i<value.length){if(value[i]===targetText[i]){spans[i].classList.add('correct');correct++}else{spans[i].classList.add('wrong');mistakes++}}else if(i===value.length){spans[i].classList.add('current')}}const elapsedMinutes=startedAt?Math.max((performance.now()-startedAt)/60000,1/6000):0;const wpm=startedAt?Math.round((correct/5)/elapsedMinutes):0;const accuracy=value.length?Math.round((correct/value.length)*100):100;$('#liveWpm').textContent=String(wpm);$('#liveAccuracy').textContent=`${accuracy}%`;if(value===targetText)finishRound(wpm,accuracy,mistakes)}
function finishRound(wpm,accuracy,mistakes){if(state!=='playing')return;state='complete';$('#typingZone').classList.add('hidden');$('#typingZone').replaceChildren();const points=Math.max(0,Math.round(wpm*2+accuracy/2-mistakes));stats.rounds=(Number(stats.rounds)||0)+1;stats.bestWpm=Math.max(Number(stats.bestWpm)||0,wpm);stats.totalPoints=(Number(stats.totalPoints)||0)+points;stats.totalAccuracy=(Number(stats.totalAccuracy)||0)+accuracy;saveStats();setStatus(language==='ar'?'جولة مكتملة':'Round complete');try{if(navigator.vibrate)navigator.vibrate(16)}catch{}reply(`${t('success')} ${wpm} ${t('wpm')} · ${accuracy}% ${t('accuracy')} · +${points} ${t('score')}`,{result:true,resultButtons:[{label:t('next'),action:'again',value:''},{label:t('back'),action:'menu',value:''}]})}
function stopBot(showAck=true){clearTimers();muted=true;state='stopped';targetText='';startedAt=0;$('#typingZone').replaceChildren();$('#typingZone').classList.add('hidden');$$('[data-thinking="true"]').forEach(node=>node.remove());setStatus(language==='ar'?'متوقف':'Paused',true);if(showAck){addMessage(t('stopped'),'bot',{system:true})}}
function resumeBot(){clearTimers();muted=false;state='idle';setStatus(language==='ar'?'جاهز للتدريب':'Ready to practice');addMessage(t('resumed'),'bot');showMenu()}
function findGame(text){const normalized=canonicalCommand(text);const aliases={سوالف:'stories',جريده:'news',جريدة:'news',تكرار:'repeat',جمل:'sentences',stories:'stories',story:'stories',news:'news',newspaper:'news',repeat:'repeat',sentences:'sentences',sentence:'sentences'};return aliases[normalized]||null}
function findDifficulty(text){const normalized=canonicalCommand(text);if(['سهل','easy'].includes(normalized))return'easy';if(['متوسط','medium','normal'].includes(normalized))return'medium';if(['صعب','hard','difficult'].includes(normalized))return'hard';return null}
function sendMessage(value){const raw=value.trim();if(!raw)return;$('#chatInput').value='';const normalized=canonicalCommand(raw);const startCommands=['ابدا','ابدأ','start','begin'];const stopCommands=['وقف','توقف','stop','cancel'];if(stopCommands.includes(normalized)){if(!muted){addMessage(raw,'user');stopBot(true)}return}if(startCommands.includes(normalized)){if(muted){resumeBot();return}addMessage(raw,'user');showMenu();return}if(muted)return;const game=findGame(raw);if(game){if(state==='playing'||state==='countdown'||state==='loading')cancelRound();startGame(game);return}if(state==='repeat-count'){addMessage(raw,'user');acceptRepeatCount(raw);return}if(state==='difficulty'){addMessage(raw,'user');const level=findDifficulty(raw);if(level){chooseDifficulty(level)}else reply(t('chooseDifficulty'),{choices:STRINGS[language].difficulty.map(([label,value])=>({label,action:'difficulty',value})),choiceType:'level'});return}if(state==='playing'){addMessage(raw,'user');reply(t('typePrompt'));return}addMessage(raw,'user');if(state==='idle'||state==='complete')reply(t('unknown'))}
const FEATURE_UI={
  ar:{leaderboard:['المتصدرون','ستُعرض النتائج المشتركة بعد إضافة حسابات وخادم آمن.'],community:['المجتمع','ملفات المستخدمين والتفاعل والرسائل قيد التجهيز، ولن تُعرض بيانات محلية على أنها مجتمع مشترك.'],vip:['VIP','العضويات والمزايا المدفوعة قيد التجهيز. لا يوجد شراء أو طلب لبيانات دفع في هذا الإصدار.'],account:['الحساب','تسجيل الدخول وإنشاء الحساب سيُتاحان بعد إعداد خادم آمن؛ لا تدخل بيانات اعتماد هنا الآن.'],coming:'قيد التجهيز',login:'تسجيل الدخول',register:'إنشاء حساب',vipAction:'عرض مزايا VIP'},
  en:{leaderboard:['Leaderboard','Shared rankings will appear after secure accounts and a backend are available.'],community:['Community','Profiles, messaging, and social features are being prepared; local data will not be presented as a shared community.'],vip:['VIP','Membership and paid benefits are being prepared. This version does not offer purchases or request payment details.'],account:['Account','Sign-in and account creation will be available after a secure backend is in place. Do not enter credentials here yet.'],coming:'Coming soon',login:'Sign in',register:'Create account',vipAction:'Explore VIP'},
};
function renderSide(){const side=$('#sideContent');if(!side)return;if(['leaderboard','community','vip','account'].includes(activeTab)){const feature=FEATURE_UI[language][activeTab];const actions=activeTab==='account'?`<div class="feature-actions"><button disabled>${FEATURE_UI[language].login}</button><button disabled>${FEATURE_UI[language].register}</button></div>`:activeTab==='vip'?`<div class="feature-actions"><button disabled>${FEATURE_UI[language].vipAction}</button></div>`:'';side.innerHTML=`<h2>${feature[0]}</h2><div class="feature-placeholder"><span class="feature-badge">${FEATURE_UI[language].coming}</span><p>${feature[1]}</p>${actions}</div>`;return}if(activeTab==='stats'){const avg=stats.rounds?Math.round((Number(stats.totalAccuracy)||0)/stats.rounds):0;side.innerHTML=`<h2>${language==='ar'?'ملخص التقدم':'Progress summary'}</h2><div class="stats-grid"><div class="stat"><span>${t('count')}</span><strong>${Number(stats.rounds)||0}</strong></div><div class="stat"><span>${t('best')}</span><strong>${Number(stats.bestWpm)||0}</strong></div><div class="stat"><span>${t('accuracy')}</span><strong>${avg}%</strong></div><div class="stat"><span>${t('total')}</span><strong>${Number(stats.totalPoints)||0}</strong></div></div>${stats.rounds?'':`<p style="margin-top:12px">${t('emptyStats')}</p>`}`;return}if(activeTab==='settings'){side.innerHTML=`<h2>${t('settings')}</h2><div class="setting-row"><span>${t('theme')}</span><select id="themeSelect"><option value="dark">${t('dark')}</option><option value="light">${t('light')}</option></select></div><div class="setting-row"><span>${t('language')}</span><select id="languageSelect"><option value="ar">${t('arabic')}</option><option value="en">${t('english')}</option></select></div><div class="setting-row"><span>${language==='ar'?'البيانات':'Data'}</span><button class="text-button" id="resetStats">${t('reset')}</button></div>`;$('#themeSelect').value=theme;$('#languageSelect').value=language;$('#themeSelect').addEventListener('change',event=>{theme=event.target.value;safeWrite('mrtyping.theme',theme);applyPreferences()});$('#languageSelect').addEventListener('change',event=>{language=event.target.value;safeWrite('mrtyping.language',language);applyPreferences()});$('#resetStats').addEventListener('click',()=>{if(confirm(t('resetConfirm'))){stats={rounds:0,bestWpm:0,totalPoints:0,totalAccuracy:0};saveStats();addMessage(t('resetDone'),'bot',{system:true})}});return}const avg=stats.rounds?Math.round((Number(stats.totalAccuracy)||0)/stats.rounds):0;side.innerHTML=`<h2>${language==='ar'?'لمحة سريعة':'Quick stats'}</h2><div class="stats-grid"><div class="stat"><span>${t('count')}</span><strong>${Number(stats.rounds)||0}</strong></div><div class="stat"><span>${t('best')}</span><strong>${Number(stats.bestWpm)||0}</strong></div></div><p style="margin-top:12px">${language==='ar'?`متوسط الدقة ${avg}% — اكتب «ابدا» واختر لعبتك التالية.`:`Average accuracy ${avg}% — type “start” to choose your next game.`}</p>`}
const STATIC_UI={
  ar:{title:'رفيق الكتابة',caption:'تدريب خفيف، تقدّم واضح',chatPanel:'محادثة التدريب',newChat:'بدء محادثة جديدة',chatInput:'أرسل رسالة إلى رفيق الكتابة',send:'إرسال',sidePanel:'لوحة المعلومات',space:'مساحتك',tabs:'الأقسام',homeTab:'التدريب',statsTab:'إحصاءاتي',settingsTab:'الإعدادات',leaderboardTab:'المتصدرون',communityTab:'المجتمع',vipTab:'VIP',accountTab:'الحساب',howTo:'طريقة اللعب',quickNote:'اكتب ابدا لعرض الألعاب، أو اختر اللعبة مباشرة. وفي أي وقت اكتب وقف لإيقاف الجولة.',footer:'mr.typing · بيانات التدريب محفوظة على هذا الجهاز فقط'},
  en:{title:'Typing buddy',caption:'Light practice, visible progress',chatPanel:'Practice chat',newChat:'Start a new chat',chatInput:'Send a message to your typing buddy',send:'Send',sidePanel:'Information panel',space:'Your space',tabs:'Sections',homeTab:'Practice',statsTab:'My stats',settingsTab:'Settings',leaderboardTab:'Leaderboard',communityTab:'Community',vipTab:'VIP',accountTab:'Account',howTo:'How to play',quickNote:'Type start to see the games or choose one directly. Type stop at any time to pause the round.',footer:'mr.typing · Training data stays on this device'}
};
function applyStaticText(){const labels=STATIC_UI[language];$('#botTitle').textContent=labels.title;$('#botCaption').textContent=labels.caption;$('#spaceTitle').textContent=labels.space;$('#quickTitle').textContent=labels.howTo;$('#quickNoteText').textContent=labels.quickNote;$('#footerText').textContent=labels.footer;$('#chatPanel').setAttribute('aria-label',labels.chatPanel);$('#clearChat').setAttribute('aria-label',labels.newChat);$('#clearChat').title=labels.newChat;$('#chatInput').setAttribute('aria-label',labels.chatInput);$('#sendButton').setAttribute('aria-label',labels.send);$('#sidePanel').setAttribute('aria-label',labels.sidePanel);$('#tabs').setAttribute('aria-label',labels.tabs);$$('[data-ui]').forEach(node=>node.textContent=labels[node.dataset.ui])}
function applyPreferences(){document.documentElement.lang=language;document.documentElement.dir=language==='ar'?'rtl':'ltr';document.documentElement.dataset.theme=theme;applyStaticText();$('#chatInput').placeholder=t('commandPlaceholder');renderSide();if(chatStarted){clearTimers();muted=false;cancelRound();$('#chatLog').replaceChildren();showMenu()}}
$('#chatForm').addEventListener('submit',event=>{event.preventDefault();sendMessage($('#chatInput').value)});
$('#chatLog').addEventListener('click',event=>{const button=event.target.closest('button[data-action]');if(!button)return;const {action,value}=button.dataset;if(action==='game')startGame(value);else if(action==='difficulty'){addMessage(displayLevel(value),'user');chooseDifficulty(value)}else if(action==='menu')showMenu();else if(action==='again')startGame(currentGame)});
$('#clearChat').addEventListener('click',()=>{clearTimers();muted=false;cancelRound();$('#chatLog').replaceChildren();chatStarted=true;showMenu()});
$$('.tab').forEach(button=>button.addEventListener('click',()=>{$$('.tab').forEach(tab=>{tab.classList.toggle('active',tab===button);tab.setAttribute('aria-selected',String(tab===button))});activeTab=button.dataset.tab;renderSide()}));
function initialize(){document.documentElement.lang=language;document.documentElement.dir=language==='ar'?'rtl':'ltr';document.documentElement.dataset.theme=theme;applyStaticText();$('#chatInput').placeholder=t('commandPlaceholder');renderSide();chatStarted=true;showMenu()}
initialize();
</script>
</body>
</html>'''


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
